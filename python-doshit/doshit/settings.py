import os
import json_serializer as json

REDIS_CONNECTION = json.load(os.getenv('DOSHIT_REDIS',
                                       '{"host": "localhost", "port": 6379, "db": 0 }'))

QUEUE_NAME = os.getenv('DOSHIT_QUEUE', 'doshit')
