import os
import redis

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

# redis = redis.StrictRedis(host=rdb_url.hostname, port=rdb_url.port, db=0, password=rdb_url.password)
redis = redis.StrictRedis.from_url(redis_url)