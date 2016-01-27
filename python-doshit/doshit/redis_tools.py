from redis import TimeoutError
from redis import ConnectionError
from redis import BusyLoadingError
from time import sleep
import ctypes

_libc = ctypes.cdll.LoadLibrary(None)
res_init = _libc.__res_init

class block_until_connection(object):
    """
    if the wrapped function calls redis and gets a redis connection error, the
    function will be called after sleeping (1,2,3 seconds) again until a
    connection is made again.
    """
    def __init__(self, terminate_event=None, logger=None):
        self.terminate_event = terminate_event
        self.logger = logger

    def __call__(self, func):
        def wrapped_f(*args, **kwargs):
            attempt = 0
            while self.terminate_event is None or not self.terminate_event.is_set():
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError, BusyLoadingError):
                    attempt += 1
                    if self.logger:
                        self.logger.info('redis connection issue when calling {0}() attempt:{1}'.format(func.func_name, attempt))
                    if attempt == 1:
                        sleep(1)
                    elif attempt == 2:
                        sleep(3)
                    else:
                        sleep(3)
                    # this resets libc reslove to go check for new /etc/resolv.conf
                    # just incase someone disable the network manager or something
                    # simalar.
                    res_init()
                    continue
        return wrapped_f
