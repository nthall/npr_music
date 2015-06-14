""" app settings, celery scheduling """
from celery.schedules import crontab

DEBUG = False
MONGODB_SETTINGS = {'DB': 'npr_music'}

SECRET_KEY = 'meh, whatever'

ECHONEST_RATE_LIMIT = 20

CELERY_ANNOTATIONS = {
    'scraper.echonest_data': {
        'rate_limit': '{0}/m'.format(ECHONEST_RATE_LIMIT)
    }
}
CELERY_BROKER_URL = 'mongodb://localhost/npr_music'
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'json'
CELERYBEAT_SCHEDULE = {
    'scrape daily': {
        'task': 'scraper.daily_update',
        'schedule': crontab(minute='*/10')
    },
    'get missing fields': {
        'task': 'scraper.missing_fields',
        'schedule': crontab()
    }
}

SCRAPE_TARGETS = ['all-things-considered']
