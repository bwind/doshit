from tasks import add
from tasks import echo
from tasks import error

# to override doshit seting you can do the following
#import doshit.settings as s
#s.DOSHIT_QUEUE = 'other'

add_result = add.delay(1, 2)
echo_result = echo.delay('shit yeeah')
error_result = error.delay()

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
