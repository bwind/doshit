import settings

import json_serializer as json
from json_serializer import strftime

from common import create_redis_connection
from common import __version__

from common import get_task_hash_key
from common import get_pending_list_key
from common import get_executing_list_key
from common import get_results_channel_key
from common import get_command_channel_key
from common import get_worker_hash_key

from common import TASK_HKEY_FUNCTION
from common import TASK_HKEY_STATE
from common import TASK_HKEY_ARGS
from common import TASK_HKEY_PENDING_CREATED
from common import TASK_HKEY_EXECUTING_CREATED
from common import TASK_HKEY_FINISHED_CREATED
from common import TASK_HKEY_RESULT
from common import TASK_HKEY_RESULT_VALUE
from common import TASK_HKEY_ERROR_REASON
from common import TASK_HKEY_ERROR_EXCEPTION
from common import TASK_HKEY_VIRTUAL_MEMORY_LIMIT

from common import STATE_PENDING
from common import STATE_EXECUTING
from common import STATE_FINISHED
from common import RESULT_SUCCESSFUL
from common import RESULT_FAILED

from multiprocessing import Process
from os_tools import set_virtual_memory_limit
from redis_tools import block_until_connection

import os
import sys
import signal
import psutil
import argparse
import traceback
from uuid import uuid4
from datetime import datetime
from socket import gethostname
from importlib import import_module
from time import sleep

@block_until_connection
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


def _deregister_worker_with_timeout(worker_uuid, timeout=2):
    redis = create_redis_connection(timeout=timeout)
    redis.delete(get_worker_hash_key(worker_uuid))

def _set_task_finished_no_blocking(redis,
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None):
    results_channel_key = get_results_channel_key()
    executing_list_key = get_executing_list_key(queue)

    task = {TASK_HKEY_STATE: STATE_FINISHED,
            TASK_HKEY_RESULT: result,
            TASK_HKEY_FINISHED_CREATED: strftime(datetime.utcnow())}

    if result_value:
        task[TASK_HKEY_RESULT_VALUE] = result_value

    if error_reason:
        task[TASK_HKEY_ERROR_REASON] = error_reason

    if error_exception:
        task[TASK_HKEY_ERROR_EXCEPTION] = error_exception

    pipe = redis.pipeline(transaction=True)
    pipe.hmset(task_hash_key, task)
    pipe.lrem(executing_list_key, task_id, 0)
    pipe.execute()

    print 'pub ' + results_channel_key + ' ' + task_hash_key
    redis.publish(results_channel_key, task_hash_key)

    print '\nresult:{0}\nresult-value:{1}\nerror-reason:{2}\n'.format(result, result_value, error_reason)

@block_until_connection
def _set_task_finished(redis,
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None):

    _set_task_finished_no_blocking(redis,
                                   queue,
                                   task_id,
                                   task_hash_key,
                                   result,
                                   result_value,
                                   error_reason,
                                   error_exception)

def _set_task_finished_with_timeout(
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None,
                  timeout=6):

    redis = create_redis_connection(timeout=timeout)
    _set_task_finished_no_blocking(redis,
                                   queue,
                                   task_id,
                                   task_hash_key,
                                   result,
                                   result_value,
                                   error_reason,
                                   error_exception)


@block_until_connection
def _set_task_exexcuting(redis, task_hash_key):
    redis.hmset(task_hash_key,
                {TASK_HKEY_STATE: STATE_EXECUTING,
                TASK_HKEY_EXECUTING_CREATED: strftime(datetime.utcnow())})

@block_until_connection
def _subscribe_to_cmd_pubsub(redis):
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(get_command_channel_key())
    return pubsub

@block_until_connection
def _get_next_task_id(redis, queue, timeout=1):
    return redis.brpoplpush(get_pending_list_key(queue),
                            get_executing_list_key(queue),
                            timeout=timeout)

@block_until_connection
def _poll_kill_task(cmd_pubsub, task_hash_key):
    message = cmd_pubsub.get_message()
    if message:
        message = message['data']
        if (message == 'task:kill:all'):
            return True
        elif (message.startswith('task:kill:')
            and task_hash_key == message.replace('task:kill:', '')):
            return True
    return False

def _exexcute_task(module, queue, task_id, task_hash_key):

    redis = create_redis_connection()
    try:
        task = redis.hmget(task_hash_key,
                            (TASK_HKEY_FUNCTION,
                            TASK_HKEY_STATE,
                            TASK_HKEY_ARGS,
                            TASK_HKEY_VIRTUAL_MEMORY_LIMIT))
        print task

        function = task[0]
        state = task[1]
        args = task[2]
        virtual_memory_limit = task[3]

        if function is None or len(function) == 0:
            _set_task_finished(redis, queue, task_id, task_hash_key,
                          RESULT_FAILED,
                          error_reason='for function to execute was not supplied')
            return

        elif state != STATE_PENDING:
            _set_task_finished(redis, queue, task_id, task_hash_key,
                          RESULT_FAILED,
                          error_reason='to execute a task its state must be "{0}" not "{1}"'.format(STATE_PENDING,
                                                                                                    state))
            return

        _set_task_exexcuting(redis, task_hash_key)

        print 'executing task_id:{0}\nfunction: {1}\nargs: {2}\n virtual_memory_limit:{3}\n'.format(task_id,
                                                                         function,
                                                                         args,
                                                                         virtual_memory_limit)
        print '--------------------------------------'

        if virtual_memory_limit:
            if isinstance(virtual_memory_limit, basestring):
                virtual_memory_limit = int(virtual_memory_limit)
            if virtual_memory_limit > 0:
                set_virtual_memory_limit(virtual_memory_limit)

        func = getattr(module, function)
        setattr(func, 'task_id', task_id)

        if args:
            result_value = func(**json.loads(args))
        else:
            result_value = func()

        if result_value:
            result_value = json.dumps(result_value, indent=2)

        _set_task_finished(redis,
                           queue,
                           task_id,
                           task_hash_key,
                           RESULT_SUCCESSFUL,
                           result_value)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        print traceback.format_exc()
        _set_task_finished(redis, queue, task_id, task_hash_key,
                      RESULT_FAILED,
                      error_reason= '{0}: {1}'.format(type(ex), ex.message),
                      error_exception=traceback.format_exc())


def worker_server(module, queue):

    pending_key = get_pending_list_key(queue)
    executing_key = get_executing_list_key(queue)

    worker_uuid = uuid4()
    redis = create_redis_connection()

    cmd_pubsub = _subscribe_to_cmd_pubsub(redis)

    _register_worker(redis, worker_uuid)

    task_id = None
    task_hash_key = None
    try:
        while True:
            task_id = _get_next_task_id(redis, queue, timeout=1)
            # if task_id is None we got a timeout
            if task_id is None:
                continue

            task_hash_key = get_task_hash_key(task_id)

            print task_hash_key

            process = Process(target=_exexcute_task,
                              args=(module, queue, task_id, task_hash_key))
            terminated = False
            killed = False
            process.start()

            while process.is_alive():
                process.join(0.2)

                if _poll_kill_task(cmd_pubsub, task_hash_key):
                    killed = True
                    break

            if process.is_alive():
                terminated = True
                process.terminate()
                process.join(1)

            if terminated:
                _set_task_finished(redis, queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    error_reason= "task was pubsub killed" if killed else "task was terminated")

            elif (not hasattr(process, '_popen')
               or not hasattr(process._popen, 'returncode')):
                _set_task_finished(redis, queue, task_id, task_hash_key,
                        RESULT_FAILED,
                        error_reason= 'task was never executed for some reason')

            elif process._popen.returncode != 0:
                _set_task_finished(redis, queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    error_reason= "task's process returncode was {0}".format(process._popen.returncode))

            task_id = None
            task_hash_key = None

    except KeyboardInterrupt:
        if (task_id is not None and task_hash_key is not None):
            _set_task_finished_with_timeout(queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    error_reason= 'task / process was killed before completion',
                    error_exception=traceback.format_exc(),
                    timeout=6)

    _deregister_worker_with_timeout(worker_uuid, timeout=2)

    cmd_pubsub.close()


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

    module_name = args.module.replace('.py', '')
    try:
        module = import_module(module_name)
    except ImportError:
        sys.path.insert(0, os.getcwd())
        module = import_module(module_name)

    settings.REDIS_CONNECTION = args.redis

    worker_server(module, args.queue)

if __name__ == "__main__":
    sys.exit(main())
