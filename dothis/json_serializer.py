import json
from datetime import datetime

"""
Subset of iso8601, using date and time down to seconds, works with moment.js lib
"""
global DATETIME_FORMATTER_RFC_3339_UTC
DATETIME_FORMATTER_RFC_3339_UTC = '%Y-%m-%dT%H:%M:%SZ'

"""
Subset of iso8601, using date and time down to micro seconds, works with moment.js lib
"""
global DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC
DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC = '%Y-%m-%dT%H:%M:%S.%fZ'


def strftime(obj):
    return obj.strftime(DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC)


def strptime(text):
    return datetime.strptime(text, DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC)


class JsonDateTimeEncoder(json.JSONEncoder):
    """
    usage:
    json.dumps({'modified-at': datetime.utcnow()}, cls=JsonDateTimeEncoder)
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"type": "datetime",
                    "value": obj.strftime(DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC)}
        else:
            return json.JSONEncoder.default(self, obj)


class JsonDateTimeDecoder(json.JSONDecoder):
    """
    usage:
    json.loads('{"date": {"type": "datetime", "value": "2015-08-10T05:57:33.113197Z"}}', cls=JsonDateTimeDecoder)
    """
    def __init__(self, *args, **kargs):
        super(JsonDateTimeDecoder, self).__init__(
            object_hook=self.dict_to_object,
            *args,
            **kargs)

    def dict_to_object(self, d):
        if 'type' not in d or 'value' not in d:
            return d
        type = d.pop('type')
        try:
            return datetime.strptime(d['value'], DATETIME_FORMATTER_RFC_3339_UTC_MICRO_SEC)
        except:
            d['type'] = type
            return d


def dump(dict, **kwargs):
    """
    returns a string / json dump for the given dictionary.
    """
    return json.dumps(dict, cls=JsonDateTimeEncoder, **kwargs)


def load(json_text, **kwargs):
    return json.loads(json_text, cls=JsonDateTimeDecoder, **kwargs)
