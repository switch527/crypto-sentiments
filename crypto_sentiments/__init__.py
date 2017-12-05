# crypto_sentiments/__init__.py

import datetime
import pickle
import threading

import schedule
from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
from crypto_sentiments.common.prices.tracking import PriceTracker
from crypto_sentiments.common.sentiments.classify import TweetClassifier
from crypto_sentiments.common.sentiments.tracking import SentimentTracker
from crypto_sentiments.models import create_db
from crypto_sentiments.models import drop_db
from crypto_sentiments.models.models import load_tables
from crypto_sentiments.models.models import save_tables
from crypto_sentiments.views.home import home
from crypto_sentiments.views.predictions import predictions_factory
from crypto_sentiments.views.visualizations import visualizations


_TRACK_FROM = datetime.datetime(2016, 1, 1)


app = Flask(__name__)


def initialize(conf, classifier_file, db_input=None):
    # config
    app.config.from_object(conf)

    # db creation
    create_db(app)
    if db_input:
        load_tables(db_input)

    # classifier
    print('### Loading classifier...')
    classifier = TweetClassifier.load(classifier_file)

    # routes
    app.register_blueprint(home)
    predictions = predictions_factory(classifier)
    app.register_blueprint(predictions, url_prefix='/predict')
    app.register_blueprint(visualizations, url_prefix='/viz')

    # track sentiment up to present
    sent_tracker = SentimentTracker(classifier, _TRACK_FROM)
    print('### Tracking sentiments...')
    sent_tracker.track(override=False) # until today, updates db
    # schedule.every().day.at("1:00").do(sent_tracker.track) # update every day

    # teack prices upto present
    price_tracker = PriceTracker(_TRACK_FROM)
    print('### Tracking prices...')
    price_tracker.track(override=False)
    # schedule.every().day.at("1:00").do(price_tracker.track) # update every day

    # optimizations
    CORS(app)
    Compress(app)


def shutdown(db_output=None):
    if db_output:
        save_tables(db_output)
    drop_db()
