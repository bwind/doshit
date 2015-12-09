import os
import json
import sys


# set default values
DOSHIT_REDIS = {"host": "localhost", "port": 6379, "db": 0 }
DOSHIT_QUEUE = 'default'
DOSHIT_APP_PREFIX = 'doshit'

# load any values that are a part of the environment varabiles.
if 'DOSHIT_REDIS' in os.environ:
    try:
        DOSHIT_REDIS = json.loads(os.environ['DOSHIT_REDIS'])
    except:
        print 'failed to load DOSHIT_REDIS json: %s' %  os.environ['DOSHIT_REDIS']

if 'DOSHIT_QUEUE' in os.environ:
    DOSHIT_QUEUE = os.environ['DOSHIT_QUEUE']

if 'DOSHIT_APP_PREFIX' in os.environ:
    DOSHIT_REDIS = os.environ['DOSHIT_APP_PREFIX']

# look for other settings.py files, if they exist load them.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.isfile(os.path.join(BASE_DIR, 'doshit_settings.py')):
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)
    from doshit_settings import *

elif os.path.exists('/etc/doshit/doshit_settings.py'):
    if '/etc/doshit' not in sys.path:
        sys.path.append('/etc/doshit')
    from doshit_settings import *
