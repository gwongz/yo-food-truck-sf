from flask import request, Flask, redirect

simpleapp = Flask(__name__)

from simpleapp import views

