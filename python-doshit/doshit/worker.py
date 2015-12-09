import settings
from common import create_redis
from common import __version__

from json_serializer import dump
from json_serializer import load
from json_serializer import strftime

from redis_keys import get_task_hash_key
from redis_keys import get_pending_list_key
from redis_keys import get_executing_list_key
from redis_keys import get_results_channel_key
from redis_keys import get_worker_hash_key

from common import STATE_PENDING
from common import STATE_EXECUTING
from common import STATE_FINISHED
from common import RESULT_SUCCESSFUL
from common import RESULT_FAILED

import os
import sys
import signal
import psutil
import argparse
import traceback
from uuid import uuid4
from threading import Event
from datetime import datetime
from socket import gethostname
from importlib import import_module


_terminate = Event()


def _register_worker(redis, worker_uuid):
    redis.hmset(get_worker_hash_key(worker_uuid),
                {
                    'hostname': gethostname(),
                    'pid': os.getpid(),
                    'cpu_cores': psutil.cpu_count(logical=True),
                    'cpu_threads': psutil.cpu_count(logical=False),
                    'virtual-mem': psutil.virtual_memory(),
                    'swap-mem': psutil.swap_memory(),
                    'registered': strftime(datetime.utcnow())
                })


def _deregister_worker(redis, worker_uuid):
    redis.delete(get_worker_hash_key(worker_uuid))


def _set_finished(redis,
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None):
    results_channel_key = get_results_channel_key()
    executing_list_key = get_executing_list_key(queue)

    task = {'state': STATE_FINISHED,
            'result': result,
            'finished-created': strftime(datetime.utcnow())}

    if result_value:
        task['result-value'] = result_value

    if error_reason:
        task['error-reason'] = error_reason

    if error_exception:
        task['error-exception'] = error_exception

    pipe = redis.pipeline(transaction=True)
    pipe.hmset(task_hash_key, task)
    pipe.lrem(executing_list_key, task_id, 0)
    pipe.execute()

    redis.publish(results_channel_key, task_hash_key)

    print '\nresult:{0}\nresult-value:{1}\nerror-reason:{2}\n'.format(result, result_value, error_reason)


def worker_server(module, queue):
    pending_key = get_pending_list_key(queue)
    executing_key = get_executing_list_key(queue)
    worker_uuid = uuid4()
    redis = create_redis()

    _register_worker(redis, worker_uuid)

    while not _terminate.is_set():

        try:
            task_id = redis.brpoplpush(pending_key, executing_key, timeout=1)
            # if task_id is none we got a timeout, so let check if we should stop our worker.
            if task_id is None:
                continue

            task_hash_key = get_task_hash_key(task_id)

            task = redis.hmget(task_hash_key, ('function', 'state', 'args'))
            function = task[0]
            state = task[1]
            args = task[2]

            if function is None or len(function) == 0:
                _set_finished(redis, queue, task_id, task_hash_key,
                              RESULT_FAILED,
                              error_reason='for function to execute was not supplied')
                continue

            elif state != STATE_PENDING:
                _set_finished(redis, queue, task_id, task_hash_key,
                              RESULT_FAILED,
                              error_reason='to execute a task its state must be "{0}" not "{1}"'.format(STATE_PENDING,
                                                                                                        state))
                continue

            else:
                redis.hmset(task_hash_key, {'state': STATE_EXECUTING, 'executing-created': strftime(datetime.utcnow())})

            print 'executing task_id:{0}\nfunction: {1}\nargs: {2}\n'.format(task_id,
                                                                             function,
                                                                             args)
            print '--------------------------------------'

            try:
                func = getattr(module, function)
                if args:
                    result_value = func(**load(args))
                else:
                    result_value = func()

                if result_value:
                    result_value = dump(result_value, indent=2)

                print '--------------------------------------'
                _set_finished(redis,
                              queue,
                              task_id,
                              task_hash_key,
                              RESULT_SUCCESSFUL,
                              result_value)

            except Exception, ex:

                print '--------------------------------------'
                _set_finished(redis, queue, task_id, task_hash_key,
                              RESULT_FAILED,
                              error_reason=ex.message,
                              error_exception=traceback.format_exc())

        except KeyboardInterrupt:
            _terminate.set()

    _deregister_worker(redis, worker_uuid)


def signal_terminate(num, stack):
    print 'singnal num:{0} stack:{1}'.format(num, stack)
    _terminate.set()
    os.kill(os.getpid(), signal.SIGINT)


def main():

    import sys
    print sys.argv

    parser = argparse.ArgumentParser(

description='This is a doshit worker, you pass it the name of the module you would like to to process',

usage='to run the example do:\n\
1) start redis-server\n\
2) cd into examples directory\n\
3) python ../doshit/worker.py tasks\n\
4) python call.py',

    version=__version__
    )

    parser.add_argument('-p', '--processes',
                        type=int,
                        default=min(psutil.cpu_count(logical=True) - 1, 1),
                        help='the cpu core count to use, default is minus one the computers physical core count.')

    parser.add_argument('-q', '--queue',
                        default=settings.DOSHIT_QUEUE,
                        help='the name of the task queue you would like to process tasks for',
                        )

    parser.add_argument('-r', '--redis',
                        default=settings.DOSHIT_REDIS,
                        help='the connection in json e.g. {"host": "localhost", "port": 6379, "db": 0 }',
                        )

    parser.add_argument('module',
                        help='the module containing the methods you wish to call.')

    args = parser.parse_args()

    module_name = args.module.rstrip('.py')

    try:
        module = import_module(module_name)
    except ImportError:
        sys.path.insert(0, os.getcwd())
        module = import_module(module_name)

    settings.REDIS_CONNECTION = args.redis

    signal.signal(signal.SIGTERM, signal_terminate)
    worker_server(module, args.queue)

if __name__ == "__main__":
    sys.exit(main())
