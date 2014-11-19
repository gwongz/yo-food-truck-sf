from flask import request, Flask, redirect

app = Flask(__name__)

from simpleapp import views

