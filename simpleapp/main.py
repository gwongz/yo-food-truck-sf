import os
from flask import request, Flask, redirect
from waitress import serve 

simpleapp = Flask(__name__)

@simpleapp.route('/')
def home():
    return 'Ok'

if __name__ == "__main__":
	#app.run()
	port = int(os.environ.get('PORT', 5000))
	serve(simpleapp, host='0.0.0.0', port=port)
