import os
import time
import calendar
import datetime
from dateutil.relativedelta import relativedelta

import oauth2
import requests
from flask import request, Flask, redirect
from helpers import *
# import keys
# from redis import Redis
# redis = Redis()
ON_DEV = not os.environ.get('HEROKU')

if ON_DEV:
    import keys 


app = Flask(__name__)

# api tokens and paths

DATA_SF = 'http://data.sfgov.org/resource/'
SF_SCHEDULE = 'jjew-r69b.json'
SF_LOCATION = 'rqzj-sfat.json'

GOOGLE_API = 'https://maps.googleapis.com/'
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', keys.google_api_key)

GOOGLE_TIMEZONE = 'maps/api/timezone/json'
GOOGLE_PLACES_SEARCH = 'maps/api/place/nearbysearch/json'
GOOGLE_PLACES_DETAIL = 'maps/api/place/details/json'

YO_API_TOKEN = os.environ.get('YO_API_TOKEN', keys.yo_api_token)

YELP_API_HOST = 'http://api.yelp.com'
SEARCH_LIMIT = 1
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

YELP_CONSUMER_KEY = os.environ.get('YELP_CONSUMER_KEY', keys.yelp_consumer_key) 
YELP_CONSUMER_SECRET = os.environ.get('YELP_CONSUMER_SECRET', keys.yelp_consumer_secret) 
YELP_TOKEN = os.environ.get('YELP_TOKEN', keys.yelp_token) 
YELP_TOKEN_SECRET = os.environ.get('YELP_TOKEN_SECRET', keys.yelp_token_secret) 

def set_lookup_dow(local_now):
    # determine what day of the week we should be searching schedule for
    dow = local_now.strftime('%A')
    hour = local_now.strftime('%H')
    minute = local_now.strftime('%M')
    # TODO: filter on open and closing time 
    if hour > 21:
        index = local_now.weekday() + 1 
        dow = index_to_day_names_map[index]
    return dow 

def lookup_timezone(latitude, longitude):

    params = {
        'location': fmt_location(latitude, longitude),
        'timestamp': calendar.timegm(time.gmtime()),
        'key': GOOGLE_API_KEY,
    }
    response_object = make_request(host=GOOGLE_API, path=GOOGLE_TIMEZONE, url_params=params)

    utc_now = datetime.datetime.utcnow()
    offset = response_object.get('dstOffset') + response_object.get('rawOffset')
    local_now = utc_now + relativedelta(seconds=offset)
    print 'local time'
    print local_now
    return set_lookup_dow(local_now)

def find_scheduled_trucks(dow):

    url_params = {
        'dayofweekstr': dow,
        'coldtruck': 'N',
        '$limit': '50000', # we want all of them
    }
    response_object = make_request(host=DATA_SF, path=SF_SCHEDULE, url_params=url_params)
    # all the location_ids for doing geosearch
    if len(response_object) == 0:
        # TODO: handle no results case  
        pass

    return response_object

def make_request(host, path='', url_params=None):
    """ Make API requests and return json response as python object """
    url = '{0}{1}'.format(host, path)
    response = requests.get(url, params=url_params)
    return response.json()

def make_signed_request(host, path='', url_params=None):
    """ Make requests for apis that required signed url """
    url = '{0}{1}'.format(host, path)
    consumer = oauth2.Consumer(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET)
    oauth_request = oauth2.Request('GET', url, url_params)
    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': YELP_TOKEN,
            'oauth_consumer_key': YELP_CONSUMER_KEY
        }
    )
    token = oauth2.Token(YELP_TOKEN, YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()
    print 'Querying Yelp {0}'.format(signed_url)
    response = requests.get(signed_url)
    return response.json()

def lookup_place_details(places_list):
    """ Look up business details for each dictionary until one with a website is found """
    print 'This is the places list, a list of dictionaries'
    place_url = []
    
    for place in places_list:
        if place_url != []:
            return place_url
        place_id = place.get('place_id')

        url_params = {
            'placeid': place_id,
            'key': GOOGLE_API_KEY
        }
        place_detail = make_request(host=GOOGLE_API, path=GOOGLE_PLACES_DETAIL, url_params=url_params)
        detail_object = place_detail.get('result')

        if detail_object:
            if detail_object.get('website'):
                website = detail_object.get('website')
                place_url.append(website)

    return place_url


def search_google_places(latitude, longitude, name):
    """ Get the business link for the food truck that we are looking for """
    location = fmt_location(latitude, longitude)
    name = fmt_name(name)

    url_params = {
        'name': name,
        'key': GOOGLE_API_KEY,
        'types': 'food',
        'location': location,
        'radius': 3200,
    }
    place_url = []
    place_objects = make_request(host=GOOGLE_API, path=GOOGLE_PLACES_SEARCH, url_params=url_params)
    places_list = place_objects.get('results')

    print place_objects
    if len(place_list) > 0:
        place_url = lookup_place_details(places_list)
    return place_url

def filter_yelp_results(response_object, term):
    place_url = []
    yelp_businesses = response_object.get('businesses')
    for business in yelp_businesses:
        if place_url != []:
            return place_url
        if business.get('name') in term and not business.get('is_closed'):
            # it is a valid business and this is their yelp address
            place_url.append(business.get('url'))
    return place_url 

def search_yelp(term, latitude=None, longitude=None, city='San Francisco', offset=0, limit=20):
    """ Given an array of response objects, find the one with the highest yelp rating """
    url_params = {
        'term': term,
        'location': city,
        'offset': offset,
        # 'cll': str(latitude) + ',' + str(longitude),
        'limit': limit,
        'sort': 0, # best matched
    }
    response_object = make_signed_request(host=YELP_API_HOST, path=SEARCH_PATH, url_params=url_params)
    place_url = filter_yelp_results(response_object, term)
    return place_url

def find_truck_website(check_against_list):
    """ Given a list of food truck names, find the best link for them via Yelp or Google """
    for truck in check_against_list:
        "Use Yelp API to make sure it is still open"
        # TODO: don't hardcode city
        place_url = search_yelp(term=truck.get('name'))
        if place_url != []:
            return place_url[0]

    for truck in check_against_list:
        latitude = truck.get('latitude')
        longitude = truck.get('longitude')
        name = truck.get('name')
        place_url = search_google_places(latitude=latitude, longitude=longitude, name=name)
        if place_url != []:
            return place_url[0]
    # not a single truck from query results has yelp profile or google places profile 
    raise Exception('Unable to find a link for trucks')


def check_proximity(scheduled_trucks, latitude, longitude, radius=1600):
    where = fmt_where_constraint(latitude, longitude, radius)
    url_params = {
        '$where': where,
        'status': 'approved'
    }
    nearby_trucks = make_request(host=DATA_SF, path=SF_LOCATION, url_params=url_params)
    nearby_ids = [x.get('objectid') for x in nearby_trucks]
    schedule_ids = [x.get('locationid') for x in scheduled_trucks]
    check_against_list = [] # a list of dictionaries 
    nearby_and_scheduled = set(nearby_ids) & set(schedule_ids)

    if len(nearby_and_scheduled) > 0:
        print 'There are trucks that are nearby and are scheduled for today '
        for truck in nearby_trucks:
            if truck['objectid'] in nearby_and_scheduled:
                d = {'name': truck['applicant'],
                    'latitude': truck['latitude'],
                    'longitude': truck['longitude']
                    }
                check_against_list.append(d)

    elif len(scheduled_trucks) > 0:
        # these are trucks that are scheduled for today but not nearby 
        for truck in locations:
            check_against_list.append({'name': truck['applicant']})
    else:
        # handle edge case if there are no trucks scheduled for the day 
        pass 

    return check_against_list

@app.route('/test')
def test():
    # test the app with hardcoded location 
    # 24 Buchanan Street
    latitude = 37.7697211
    longitude = -122.4265952

    # ferry building
    latitude = 37.795548
    longitude = -122.393413
    
    dow = lookup_timezone(latitude=latitude,longitude=longitude)
    scheduled_trucks = find_scheduled_trucks(dow)
    check_against_list = check_proximity(scheduled_trucks, latitude, longitude)
    truck_link = find_truck_website(check_against_list)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

