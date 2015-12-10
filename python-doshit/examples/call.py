from tasks import add
from tasks import echo
from tasks import error

# to override doshit seting you can do the following
#import doshit.settings as s
#s.DOSHIT_QUEUE = 'other'

add_result = add.exec_async(1, 2)
echo_result = echo.exec_async('shit yeeah')
error_result = error.exec_async()

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

add_result.close()
echo_result.close()
error_result.close()
