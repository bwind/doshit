import os
import json_serializer as json

REDIS_CONNECTION = json.load(os.getenv('DOTHIS_REDIS',
                                       '{"host": "localhost", "port": 6379, "db": 0 }'))

QUEUE_NAME = os.getenv('DOTHIS_QUEUE', 'dothis')
