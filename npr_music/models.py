""" models """

from npr_music import db


class Song(db.Document):
    """ holds one instance of a song being played on a given program/day """
    aired_on = db.DateTimeField(required=True)
    program = db.StringField(max_length=100, required=True)
    title = db.StringField(max_length=255, required=True)
    artist = db.StringField(max_length=255, required=True,
                            unique_with=('aired_on', 'program', 'title'))
    npr_duration = db.IntField()  # (in seconds)
    # album? album release date? actually kind of hard, tbd

    # echonest attributes
    tempo = db.DecimalField(precision=8)
    duration = db.DecimalField(precision=12)
    time_signature = db.IntField()
    key = db.IntField(min_value=0, max_value=11)
    mode = db.IntField(min_value=0, max_value=1)
    loudness = db.DecimalField(precision=8)
    acousticness = db.DecimalField(min_value=0, max_value=1, precision=6)
    energy = db.DecimalField(min_value=0, max_value=1, precision=6)
    valence = db.DecimalField(min_value=0, max_value=1, precision=6)
    liveness = db.DecimalField(min_value=0, max_value=1, precision=6)
    danceability = db.DecimalField(min_value=0, max_value=1, precision=6)

    def __unicode__(self):
        return self.title

# def __unicode__(self.key):
#  return string representation of key & mode?
#  return u'C'

    meta = {
        'allow_inheritance': False,
        'indexes': ['aired_on', 'program', 'artist',
                    'key', 'mode', 'time_signature']
    }
