from flask import request, Flask, redirect

app = Flask(__name__)

@app.route('/')
def home():
    return 'Ok'