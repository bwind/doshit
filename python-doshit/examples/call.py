from tasks import add
from tasks import echo
from tasks import error
from tasks import mem_error
from tasks import sleep

# to override doshit seting you can do the following
#import doshit.settings as s
#s.DOSHIT_QUEUE = 'other'

add_result = add.exec_async(1, 2)
echo_result = echo.exec_async('shit yeeah')
error_result = error.exec_async()
mem_error_result = mem_error.exec_async(virtual_memory_limit=1024)

print ''
print str(add_result)
print add_result.wait()

print ''
print str(echo_result)
print echo_result.wait()

print ''
print str(error_result)
print error_result.wait()
print ''
print error_result.error_exception

print ''
print str(mem_error_result)
print mem_error_result.wait()
print ''
print mem_error_result.error_exception

add_result.close()
echo_result.close()
error_result.close()
mem_error_result.close()

import time
sleep_result = sleep.exec_async(sleep_for=1)
time.sleep(0.1)
sleep_result.cancel()
print sleep_result.wait()
