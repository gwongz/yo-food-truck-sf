import os
import requests
from flask import request, Flask, redirect
from helpers import *
# import keys
# from redis import Redis
# redis = Redis()
ON_DEV = not os.environ.get('HEROKU')
YO_API_TOKEN = os.environ.get('YO_API_TOKEN')

app = Flask(__name__) 

@app.route('/test')
def test():
    # test the app with hardcoded location 
    # 24 Buchanan Street
    latitude = 37.7697211
    longitude = -122.4265952

    # ferry building
    # latitude = 37.795548
    # longitude = -122.393413

    # marina
    latitude=37.7985662
    longitude=-122.454006
    
    dow = lookup_timezone(latitude=latitude,longitude=longitude)
    scheduled_trucks = find_scheduled_trucks(dow)

    check_against_list = check_proximity(scheduled_trucks, latitude, longitude)
    try:
        truck_link = find_truck_website(check_against_list)
    except Exception:
        # no trucks found 
        return 'No trucks found'
    else:
        link = clean_link(truck_link)
        return redirect(link, code=302)

@app.route('/yo')
def post_yo():

    # extract and parse query parameters
    username = request.args.get('username')
    location = request.args.get('location')
    print username
    print location 
    latitude = location.split(';')[0]
    longitude = location.split(';')[1]
    dow = lookup_timezone(latitude=latitude, longitude=longitude)
    scheduled_trucks = find_scheduled_trucks(dow)
    # filtered for proximity 
    check_against_list = check_proximity(scheduled_trucks, latitude, longitude)
    truck_link = find_truck_website(check_against_list)
    link = clean_link(truck_link)
    requests.post("http://api.justyo.co/yo/", data={'api_token': YO_API_TOKEN, 'username': username, 'link': link})
   
    return 'Ok'

@app.route('/')
def home():
    return 'Ok'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, host="0.0.0.0")



