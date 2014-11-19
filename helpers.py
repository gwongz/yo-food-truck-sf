import requests 
from bs4 import BeautifulSoup

index_to_day_names_map = {
	0: 'Monday',
	1: 'Tuesday',
	2: 'Wednesday',
	3: 'Thursday',
	4: 'Friday',
	5: 'Saturday',
	6: 'Sunday'
}

def fmt_location(latitude, longitude):
	""" Format a location string to 'latitude, longitude' format for GoogleAPI calls """
	location = str(latitude) + ',' + str(longitude)
	return location

def fmt_where_constraint(latitude, longitude, radius):
	""" Format the where query parameter for Soda API """
	where = ['within_circle(location,', str(latitude), ',', str(longitude), ',', str(radius), ')']
	return ''.join(where)

def fmt_name(name):
	""" Splits food truck name into query string parameters """
	name = name.split(' ')
	return '+'.join(name)

def clean_link(link):
	""" Scrape Yelp page for business website or return website from Google Places API """
	if 'yelp' in link:
		print 'parsing yelp html'
		response = requests.get(link)
		content = response.content
		soup = BeautifulSoup(content)
		div = soup.findAll('div',{'class':'biz-website'})
		if len(div) > 0:
		    link = div[0].find('a').text
		    # should use better regex, link could start with www
		    if not link.startswith('http'):
		        link = 'http://www.' + link
	return link 


