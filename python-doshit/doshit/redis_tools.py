from redis import TimeoutError
from redis import ConnectionError
from redis import BusyLoadingError
from time import sleep
import ctypes

_libc = ctypes.cdll.LoadLibrary(None)
res_init = _libc.__res_init

def block_until_connection(func):
    """
    if the wrapped function calls redis and gets a redis connection error, the
    function will be called after sleeping (1,2,3 seconds) again until a
    connection is made again.
    """
    def func_wrapper(*args, **kwargs):
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except (TimeoutError, ConnectionError, BusyLoadingError):
                attempt += 1
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
    return func_wrapper
