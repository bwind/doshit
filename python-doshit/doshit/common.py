__version__ = '0.1.0'

from redis import Redis
import settings

STATE_PENDING = 'pending'
STATE_EXECUTING = 'executing'
STATE_FINISHED = 'finished'

RESULT_SUCCESSFUL = 'successful'
RESULT_FAILED = 'failed'

def create_redis_connection(connection_dict=None):
    print 'redis connection:'
    if connection_dict:
        print connection_dict
        return Redis(**connection_dict)
    elif settings.DOSHIT_REDIS:
        print settings.DOSHIT_REDIS
        return Redis(**settings.DOSHIT_REDIS)
    else:
        return Redis()

TASK_HKEY_FUNCTION = 'function'
TASK_HKEY_STATE = 'state'
TASK_HKEY_ARGS = 'args'
TASK_HKEY_VIRTUAL_MEMORY_LIMIT = 'virtual-memory-limit'
TASK_HKEY_USERNAME = 'username'

TASK_HKEY_PENDING_CREATED = 'pending-created'
TASK_HKEY_EXECUTING_CREATED = 'executing-created'
TASK_HKEY_FINISHED_CREATED = 'finished-created'
TASK_HKEY_RESULT = 'result'
TASK_HKEY_RESULT_VALUE = 'result-value'
TASK_HKEY_ERROR_REASON = 'error-reason'
TASK_HKEY_ERROR_EXCEPTION = 'error-exception'


def get_task_hash_key(task_id):
    return '{0}:task:{1}'.format(settings.DOSHIT_APP_PREFIX, task_id)


def get_pending_list_key(queue):
    return '{0}:{1}:pending'.format(settings.DOSHIT_APP_PREFIX, queue)


def get_executing_list_key(queue):
    return '{0}:{1}:executing'.format(settings.DOSHIT_APP_PREFIX, queue)


def get_results_channel_key():
    return '{0}:results'.format(settings.DOSHIT_APP_PREFIX)

def get_command_channel_key():
    return '{0}:cmd'.format(settings.DOSHIT_APP_PREFIX)


def get_worker_hash_key(worker_id):
    return '{0}:worker:{1}'.format(settings.DOSHIT_APP_PREFIX, worker_id)
