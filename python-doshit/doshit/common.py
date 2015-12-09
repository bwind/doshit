__version__ = '0.1.0'

from redis import Redis
import settings

STATE_PENDING = 'pending'
STATE_EXECUTING = 'executing'
STATE_FINISHED = 'finished'

RESULT_SUCCESSFUL = 'successful'
RESULT_FAILED = 'failed'

def create_redis():
    if settings.DOSHIT_REDIS:
        print 'redis connection:'
        print settings.DOSHIT_REDIS

        return Redis(**settings.DOSHIT_REDIS)
    else:
        return Redis()
