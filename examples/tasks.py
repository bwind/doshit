from dothis import task

# to override dothis seting you can do the following
#import dothis.settings as s
#s.QUEUE_NAME = 'other'

@task
def add(a, b):
    print 'adding {0} {1}'.format(a, b)
    return a + b


@task
def echo(text):
    return text


@task
def error():
    raise ValueError('you ant got no values bro')
