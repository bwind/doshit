import os
import json
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

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
if os.path.exists('/etc/doshit/settings.py'):
    from local_settings import *

if os.path.isfile(os.path.join(BASE_DIR, 'local_settings.py')):
    from local_settings import *
