from uuid import uuid1
from datetime import datetime

import doshit.settings
from doshit.common import create_redis_connection
from doshit.common import STATE_PENDING
from doshit.common import RESULT_FAILED
from doshit.common import RESULT_SUCCESSFUL

from doshit.common import TASK_HKEY_FUNCTION
from doshit.common import TASK_HKEY_STATE
from doshit.common import TASK_HKEY_ARGS
from doshit.common import TASK_HKEY_USERNAME
from doshit.common import TASK_HKEY_VIRTUAL_MEMORY_LIMIT
from doshit.common import TASK_HKEY_PENDING_CREATED
from doshit.common import TASK_HKEY_RESULT
from doshit.common import TASK_HKEY_RESULT_VALUE
from doshit.common import TASK_HKEY_ERROR_REASON
from doshit.common import TASK_HKEY_ERROR_EXCEPTION

from doshit.common import get_task_hash_key
from doshit.common import get_pending_list_key
from doshit.common import get_results_channel_key
from doshit.common import get_command_channel_key

import doshit.json_serializer as json

from inspect import getcallargs


def canel_task(redis, task_id):
    redis.publish(get_command_channel_key(),
                 'task:kill:{0}'.format(get_task_hash_key(task_id)))


class AsyncResult(object):

    def __init__(self, redis, pubsub, task_hash_key, task_id):
        self._redis = redis
        self._pubsub = pubsub
        self._task_hash_key = task_hash_key
        self.task_id = task_id
        self.result = None
        self.result_value = None
        self.error_reason = None
        self.error_exception = None

    def __str__(self):
        return self._task_hash_key

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def cancel(self):
        canel_task(self._redis, self.task_id)

    def close(self):
        if self._pubsub:
            self._pubsub.close()
            self._pubsub = None

    def get_result(self):
        if self.result == RESULT_SUCCESSFUL:
            return (self.result, self.result_value)

        if self.result == RESULT_FAILED:
            return (self.result, self.error_reason)

        else:
            return (None, None)

    def poll(self):

        if self.result:
            return self.get_result()

        (self.result,
         result_value,
         self.error_reason,
         self.error_exception) = self._redis.hmget(self._task_hash_key,
                                                    (TASK_HKEY_RESULT,
                                                     TASK_HKEY_RESULT_VALUE,
                                                     TASK_HKEY_ERROR_REASON,
                                                     TASK_HKEY_ERROR_EXCEPTION))

        if result_value:
            self.result_value = json.loads(result_value)

        return self.get_result()

    def wait(self):

        if self.result is None:

            for message in self._pubsub.listen():

                if (message is None or
                        'data' not in message or
                        message['data'] != self._task_hash_key):
                    continue

                return self.poll()

        return self.get_result()


class task(object):
    """
    this is the task decorator.
    """
    def __init__(self,
                 username=None,
                 task_id=None,
                 app_prefix=settings.DOSHIT_APP_PREFIX,
                 queue=settings.DOSHIT_QUEUE,
                 virtual_memory_limit=settings.DOSHIT_TASK_VIRTUAL_MEMORY_LIMIT,
                 execute_time_limit=None,
                 result_time_to_live=None,
                 attributes={},
                 redis_connection=settings.DOSHIT_REDIS):

        self.username = username
        self.task_id = task_id
        self.app_prefix = app_prefix
        self.queue = queue
        self.virtual_memory_limit = virtual_memory_limit
        self.execute_time_limit = execute_time_limit
        self.result_time_to_live = result_time_to_live
        self.attributes = attributes
        self.redis_connection = redis_connection

    def __call__(self, f):
        f.exec_async = self.exec_async
        f.task = self
        self.func = f
        return f

    def exec_async(self, *args, **kwargs):
        if self.task_id:
            task_id = self.task_id
        else:
            task_id = uuid1()
        print(self.func)
        args_json = json.dumps(getcallargs(self.func, *args, **kwargs), indent=2)

        redis = create_redis_connection(self.redis_connection)

        task_hash_key = get_task_hash_key(task_id)
        pending_list_key = get_pending_list_key(self.queue)
        results_channel_key = get_results_channel_key()

        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(results_channel_key)

        pipe = redis.pipeline(transaction=True)

        pipe.lpush(pending_list_key, task_id)

        print(self.virtual_memory_limit)

        pipe.hmset(task_hash_key,
                   {TASK_HKEY_FUNCTION: self.func.__name__,
                   TASK_HKEY_ARGS: args_json,
                   TASK_HKEY_STATE: STATE_PENDING,
                   TASK_HKEY_USERNAME: self.username,
                   TASK_HKEY_PENDING_CREATED: json.strftime(datetime.utcnow()),
                   TASK_HKEY_VIRTUAL_MEMORY_LIMIT: self.virtual_memory_limit})

        pipe.execute()

        return AsyncResult(redis, pubsub, task_hash_key, task_id)
