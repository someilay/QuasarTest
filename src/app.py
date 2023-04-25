from flask import Flask
from src.views.base import base
from src.views.metrics import metrics


# App

app = Flask(__name__)
app.register_blueprint(base, url_prefix='/')
app.register_blueprint(metrics, url_prefix='/')
