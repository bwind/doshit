__version__ = '0.1.0'

from redis import Redis
import settings

STATE_PENDING = 'pending'
STATE_EXECUTING = 'executing'
STATE_FINISHED = 'finished'

RESULT_SUCCESSFUL = 'successful'
RESULT_FAILED = 'failed'

def create_redis():
    if settings.REDIS_CONNECTION:
        print 'redis connection:'
        print settings.REDIS_CONNECTION

        return Redis(**settings.REDIS_CONNECTION)
    else:
        return Redis()
