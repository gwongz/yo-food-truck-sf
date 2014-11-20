import os
import redis
import urlparse

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
url = urlparse.urlparse(redis_url)
redis = redis.StrictRedis(host=url.hostname, port=url.port, db=0, password=url.password)
