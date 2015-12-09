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
    return text


@task
def error():
    raise ValueError('you ant got no values bro')
