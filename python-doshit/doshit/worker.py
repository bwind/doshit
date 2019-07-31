import doshit.settings as settings

import doshit.json_serializer as json
from doshit.json_serializer import strftime

from doshit.common import create_redis_connection
from doshit.common import __version__

from doshit.common import get_task_hash_key
from doshit.common import get_pending_list_key
from doshit.common import get_executing_list_key
from doshit.common import get_results_channel_key
from doshit.common import get_command_channel_key
from doshit.common import get_worker_hash_key

from doshit.common import TASK_HKEY_FUNCTION
from doshit.common import TASK_HKEY_STATE
from doshit.common import TASK_HKEY_ARGS
from doshit.common import TASK_HKEY_PENDING_CREATED
from doshit.common import TASK_HKEY_EXECUTING_CREATED
from doshit.common import TASK_HKEY_FINISHED_CREATED
from doshit.common import TASK_HKEY_RESULT
from doshit.common import TASK_HKEY_RESULT_VALUE
from doshit.common import TASK_HKEY_ERROR_REASON
from doshit.common import TASK_HKEY_ERROR_EXCEPTION
from doshit.common import TASK_HKEY_VIRTUAL_MEMORY_LIMIT

from doshit.common import STATE_PENDING
from doshit.common import STATE_EXECUTING
from doshit.common import STATE_FINISHED
from doshit.common import RESULT_SUCCESSFUL
from doshit.common import RESULT_FAILED

from multiprocessing import Process
from doshit.os_tools import set_virtual_memory_limit
from doshit.redis_tools import block_until_connection

import os
import sys
import signal
import argparse
import traceback
from threading import Event
from uuid import uuid4
from datetime import datetime
from socket import gethostname, gethostbyname
from importlib import import_module
from time import sleep

import logging, uuid

_terminate = Event()

def _create_logger(log_level=logging.INFO, log_file=None):
    """
    creates a unique logger
    """
    fmt = '%(asctime)s %(levelname)s: %(message)s'
    datefmt = '[%Y-%m-%d %H:%M:%S]'

    logging.basicConfig(format=fmt,
                        datefmt=datefmt,
                        level=log_level)


    logger = logging.getLogger(str(uuid.uuid4()))
    if log_file:
        handler = logging.FileHandler(filename=log_file)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        logger.addHandler(handler)

    return logger

@block_until_connection(terminate_event=_terminate)
def _register_worker(redis, worker_uuid):
    hostname = gethostname()
    try:
        ipaddress = gethostbyname(hostname)
    except:
        ipaddress = ""

    redis.hmset(get_worker_hash_key(worker_uuid),
                {
                    'hostname': hostname,
                    'ipaddress': ipaddress,
                    'pid': os.getpid(),
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
                  error_exception=None,
                  logger=None):
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
    pipe.lrem(executing_list_key, 0, task_id)
    pipe.execute()

    print('pub ' + results_channel_key + ' ' + task_hash_key)
    redis.publish(results_channel_key, task_hash_key)

    if logger:
        logger.info('result:{0}\nresult-value:{1}\nerror-reason:{2}\n'.format(result, result_value, error_reason))

@block_until_connection(terminate_event=_terminate)
def _set_task_finished(redis,
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None,
                  logger=None):

    _set_task_finished_no_blocking(redis,
                                   queue,
                                   task_id,
                                   task_hash_key,
                                   result,
                                   result_value,
                                   error_reason,
                                   error_exception,
                                   logger=logger)

def _set_task_finished_with_timeout(
                  queue,
                  task_id,
                  task_hash_key,
                  result=True,
                  result_value=None,
                  error_reason=None,
                  error_exception=None,
                  logger=None,
                  timeout=6):

    redis = create_redis_connection(timeout=timeout)
    _set_task_finished_no_blocking(redis,
                                   queue,
                                   task_id,
                                   task_hash_key,
                                   result,
                                   result_value,
                                   error_reason,
                                   error_exception,
                                   logger=logger)


@block_until_connection(terminate_event=_terminate)
def _set_task_exexcuting(redis, task_hash_key):
    redis.hmset(task_hash_key,
                {TASK_HKEY_STATE: STATE_EXECUTING,
                TASK_HKEY_EXECUTING_CREATED: strftime(datetime.utcnow())})

@block_until_connection(terminate_event=_terminate)
def _subscribe_to_cmd_pubsub(redis):
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(get_command_channel_key())
    return pubsub

@block_until_connection(terminate_event=_terminate)
def _get_next_task_id(redis, queue, timeout=1):
    return redis.brpoplpush(get_pending_list_key(queue),
                            get_executing_list_key(queue),
                            timeout=timeout)

@block_until_connection(terminate_event=_terminate)
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
    logger = _create_logger()
    try:
        task = redis.hmget(task_hash_key,
                            (TASK_HKEY_FUNCTION,
                            TASK_HKEY_STATE,
                            TASK_HKEY_ARGS,
                            TASK_HKEY_VIRTUAL_MEMORY_LIMIT))
        print(task)

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

        logger.info('executing task_id:{0}\nfunction: {1}\nargs: {2}\n virtual_memory_limit:{3}\n'.format(task_id,
                                                                         function,
                                                                         args,
                                                                         virtual_memory_limit))
        logger.info('--------------------------------------')

        if virtual_memory_limit:
            if isinstance(virtual_memory_limit, str):
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
                           result_value,
                           logger=logger)

    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt _exexcute_task')

    except Exception as ex:
        logger.info(traceback.format_exc())
        _set_task_finished(redis, queue, task_id, task_hash_key,
                      RESULT_FAILED,
                      logger=logger,
                      error_reason= '{0}: {1}'.format(type(ex), ex.message),
                      error_exception=traceback.format_exc())


def _kill_process(process, logger=None):
    if process is not None:
        if logger is not None:
            logger.info('killing process pid: {0}'.format(process.pid))
        if process.is_alive():
            os.kill(process.pid, signal.SIGINT)
            process.join(1)
        if process.is_alive():
            os.kill(process.pid, signal.SIGTERM)
            process.join(1)
        if process.is_alive():
            os.kill(process.pid, signal.SIGKILL)

def worker_server(module, queue):

    worker_uuid = uuid4()
    redis = create_redis_connection()

    logger = _create_logger()
    logger.info('worker:{0} pid: {1} started'.format(worker_uuid, os.getpid()))

    cmd_pubsub = _subscribe_to_cmd_pubsub(redis)

    _register_worker(redis, worker_uuid)

    task_id = None
    task_hash_key = None
    process = None
    try:
        while not _terminate.is_set():
            task_id = _get_next_task_id(redis, queue, timeout=1)
            # if task_id is None we got a timeout
            if task_id is None:
                continue

            task_hash_key = get_task_hash_key(task_id)

            print(task_hash_key)
            logger.info('wtf')
            process = Process(target=_exexcute_task,
                              args=(module, queue, task_id, task_hash_key))
            terminated = False
            killed = False
            process.start()

            while process.is_alive() and not _terminate.is_set():
                process.join(0.2)

                if _poll_kill_task(cmd_pubsub, task_hash_key):
                    killed = True
                    break

            if _terminate.is_set():
                break

            if process.is_alive():
                terminated = True
                _kill_process(process, logger)

            if terminated:
                _set_task_finished(redis, queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    logger=logger,
                    error_reason= "task was pubsub killed" if killed else "task was terminated")

            elif (not hasattr(process, '_popen')
               or not hasattr(process._popen, 'returncode')):
                _set_task_finished(redis, queue, task_id, task_hash_key,
                        RESULT_FAILED,
                        logger=logger,
                        error_reason= 'task was never executed for some reason')

            elif process._popen.returncode != 0:
                _set_task_finished(redis, queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    logger=logger,
                    error_reason= "task's process returncode was {0}".format(process._popen.returncode))

            if _terminate.is_set():
                break

            task_id = None
            task_hash_key = None
            process = None

    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt worker')
        _terminate.set()

    if _terminate.is_set():
        if process is not None:
            _kill_process(process, logger)

        if (task_id is not None and task_hash_key is not None):
            _set_task_finished_with_timeout(queue, task_id, task_hash_key,
                    RESULT_FAILED,
                    error_reason= 'task / process was killed before completion',
                    error_exception=traceback.format_exc(),
                    timeout=6)

    _deregister_worker_with_timeout(worker_uuid, timeout=2)

    cmd_pubsub.close()

def signal_handler(signum, stack_frame):
    logger = _create_logger()
    logger.info('signal_handler {0}'.format(signum))
    logger.info('SIGINT pid: {0}'.format(os.getpid()))

    _terminate.set()
    # change terminate into SIGINT / KeyboardInterrupt
    os.kill(os.getpid(), signal.SIGINT)



def main():

    import logging
    import sys
    print(sys.argv)

    logger = _create_logger()
    logger.info('hello')

    parser = argparse.ArgumentParser(

description='This is a doshit worker, you pass it the name of the module you would like to to process',

usage='to run the example do:\n\
1) start redis-server\n\
2) cd into examples directory\n\
3) python ../doshit/worker.py tasks\n\
4) python call.py',

    prog='doshit'+__version__
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

    signal.signal(signal.SIGTERM, signal_handler)

    worker_server(module, args.queue)

if __name__ == "__main__":
    main()
