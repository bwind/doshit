from uuid import uuid4
from datetime import datetime

import settings
from common import create_redis
from common import STATE_PENDING
from common import RESULT_FAILED
from common import RESULT_SUCCESSFUL

from redis_keys import get_task_hash_key
from redis_keys import get_pending_list_key
from redis_keys import get_results_channel_key
import json_serializer as json

from inspect import getcallargs


class DelayedResult(object):

    def __init__(self, redis, pubsub, task_hash_key):
        self._redis = redis
        self._pubsub = pubsub
        self._task_hash_key = task_hash_key
        self.result = None
        self.result_value = None
        self.error_reason = None
        self.error_exception = None
        self.error_stacktrace = None

    def __str__(self):
        return self._task_hash_key

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
         self.error_exception,
         self.error_stacktrace) = self._redis.hmget(self._task_hash_key,
                                                    ('result',
                                                     'result-value',
                                                     'error-reason',
                                                     'error-exception',
                                                     'error-stacktrace'))

        if result_value:
            self.result_value = json.load(result_value)

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


def task(func):
    _func = func

    def delay(*args, **kwargs):

        args_json = json.dump(getcallargs(_func, *args, **kwargs), indent=2)

        redis = create_redis()

        task_id = kwargs.pop('task_id', str(uuid4()))
        queue = kwargs.pop('queue', settings.QUEUE_NAME)

        task_hash_key = get_task_hash_key(task_id)
        pending_list_key = get_pending_list_key(queue)
        results_channel_key = get_results_channel_key()

        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(results_channel_key)

        pipe = redis.pipeline(transaction=True)

        pipe.lpush(pending_list_key, task_id)

        pipe.hmset(task_hash_key,
                   {'function': func.__name__,
                   'state': STATE_PENDING,
                   'pending-created': json.strftime(datetime.utcnow()),
                   'args': args_json})

        pipe.execute()

        return DelayedResult(redis, pubsub, task_hash_key)

    func.delay = delay
    return func
