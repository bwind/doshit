from doshit import task

# to override doshit seting you can do the following
#import doshit.settings as s
#s.DOSHIT_QUEUE = 'other'


@task
def add(a, b):
    print 'adding {0} {1}'.format(a, b)
    return a + b


@task
def echo(text):
    if hasattr(echo, 'task_id'):
        print echo.task_id
    return text


@task
def error():
    raise ValueError('you ant got no values bro')


@task
def mem_error():
    MEGA = 10 ** 6
    MEGA_STR = ' ' * MEGA
    i = 0
    ar = []
    while i < 100:
        ar.append(MEGA_STR + str(i))


@task
def sleep(sleep_for):
    import time, sys
    time.sleep(sleep_for)
