# from app import app
# app.run(debug=True)
import os
from waitress import serve
from simpleapp import simpleapp

port = int(os.environ.get('PORT', 5000))
serve(simpleapp, host='0.0.0.0', port=port)
# simpleapp.run(host='0.0.0.0', port=port, debug=True)
 
