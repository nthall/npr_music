""" startup """
import logging
from flask import Flask
from flask.ext.mongoengine import MongoEngine

from npr_music.make_celery import make_celery

app = Flask(__name__, instance_relative_config=True,
            instance_path='/usr/src/npr_music/instance')
app.config.from_object('config')
app.config.from_pyfile('config.py')

log_handler = logging.FileHandler('app.log')
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)

db = MongoEngine(app)
celery = make_celery(app)

# import tasks


if __name__ == '__main__':
    app.run()
