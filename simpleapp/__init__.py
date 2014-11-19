from flask import request, Flask, redirect
 

simpleapp = Flask(__name__)

@simpleapp.route('/')
def home():
    return 'Ok'

