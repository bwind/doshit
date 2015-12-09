import settings

def get_task_hash_key(task_id):
    return '{0}:task:{1}'.format(settings.DOSHIT_APP_PREFIX, task_id)


def get_pending_list_key(queue):
    return '{0}:{1}:pending'.format(settings.DOSHIT_APP_PREFIX, queue)


def get_executing_list_key(queue):
    return '{0}:{1}:executing'.format(settings.DOSHIT_APP_PREFIX, queue)


def get_results_channel_key():
    return '{0}:results'.format(settings.DOSHIT_APP_PREFIX)


def get_worker_hash_key(worker_id):
    return '{0}:worker:{1}'.format(settings.DOSHIT_APP_PREFIX, worker_id)
