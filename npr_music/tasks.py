from npr_music import app, celery


@celery.task(name='scraper.daily_update')
def daily_update():
    """ wrapper for scrape_single to scrape all shows daily. """
    # note - url is way different for archive views.
    url = 'http://www.npr.org/programs/%s/?view=musicview'
    for program in app.config['SCRAPE_TARGETS']:
        target = url % program
        scrape_single.delay(target, program)


@celery.task(name='scraper.scrape_single')
def scrape_single(target, program):
    """ do the scrape - if date not in system, try scraping yesterday's """
    # TODO: breakout into smaller bits
    import requests
    from datetime import datetime
    from bs4 import BeautifulSoup
    from npr_music.models import Song

    req = requests.get(target)
    page = BeautifulSoup(req.text)

    airtime = page.find('time')
    aired_on = datetime.strptime(airtime['datetime'], '%Y-%m-%d')
    # check whether we've got a limit on dates?
    if app.config['DATE_LIMIT']:
        if aired_on < app.config['DATE_LIMIT']:
            return

    # check whether we've scraped this before
    # TODO: better check/tracking on this
    if Song.objects(aired_on=aired_on, program=program).count() > 0:
        return

    # check previous day's page.
    prev = page.find(class_='prev').find('a')
    scrape_single.delay(prev['href'], program)

    # now, process the day's songs
    songs = page.find_all(class_='musicwrap')
    for song in songs:
        # extract artist & length spans first
        artist = song.find(class_='artist').extract().text.strip()
        length = song.find(class_='duration').extract().text.strip()
        title = song.find(class_='songTitle').text.strip()
        # cheeky listcomp to get time in seconds via
        # stackoverflow.com/questions/10663720/converting-a-time-string-to-seconds-in-python
        npr_duration = sum([a*b for a, b in zip([60, 1],
                           map(int, length.split(':')))])

        song_data = {
            'title': title,
            'artist': artist,
            'length': length,
            'npr_duration': npr_duration,
            'aired_on': aired_on,
            'program': program
        }

        play = Song(**song_data)
        play.save(force_insert=True)  # don't update records that already exist

        echonest_data.delay(title, artist)


@celery.task(name='scraper.echonest_data')
def echonest_data(title, artist):
    """ get echonest info for a  track """
    # TODO: also break out into smaller bits
    import json
    import os
    import requests
    from npr_music.models import Song
    API_KEY = os.environ['ECHO_NEST_API_KEY']
    search_url = 'http://developer.echonest.com/api/v4/song/search'

    #  TODO: check whether a different worker already found this track
    #  song.objects(q_obj={'title': title, 'artist': artist,
    #                      'mode': {'$exists': False}})

    req_data = {
        'api_key': API_KEY,
        'title': title,
        'artist': artist,
        'format': 'json',
        'bucket': 'audio_summary'
    }

    req = requests.get(search_url, params=req_data)
    res = json.loads(req.text)
    app.logger.info(json.dumps(res, sort_keys=True,
                               indent=4, separators=(',', ':')))

    # check rate limit
    rate_limit = req.headers['x-ratelimit-limit']
    if rate_limit != app.config['ECHONEST_RATE_LIMIT']:
        celery.control.rate_limit('scraper.echonest_data',
                                  '{0}/m'.format(rate_limit))

    # check for search success and do the stuff with the thing
    if res['response']['status']['code'] == 0:  # success
        response = res['response']['songs']

    if len(response) > 0:
        # ugh this is annoying and bad but it gets the job done for now :/
        whitelist_fields = [
            'tempo',
            'duration',
            'time_signature',
            'key',
            'mode',
            'loudness',
            'acousticness',
            'energy',
            'valence',
            'liveness',
            'danceability'
        ]

        audio_data = {}
        summary = response[0]['audio_summary']
        for field in whitelist_fields:
            # fix for update() lacking default op, maybe pull req?
            audio_data["set__" + field] = summary[field]

            for match in Song.objects(title=title, artist=artist):
                match.update(**audio_data)

    else:
        app.logger.info(u':( no match for "{0}" by {1}'.format(title, artist))


@celery.task(name='scraper.missing_fields')
def missing_fields():
    from npr_music.models import Song

    # proxy for EN data existing - might be nice to have a better one
    incompletes = Song.objects(mode__exists=False)
    for song in incompletes:
        echonest_data.delay(song.title, song.artist)
