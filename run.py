# from app import app
# app.run(debug=True)
import os
from simpleapp import simpleapp

port = int(os.environ.get('PORT', 5000))
simpleapp.run(host='0.0.0.0', port=port, debug=True)
 
