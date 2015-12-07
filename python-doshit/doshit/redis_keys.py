

def get_task_hash_key(app_prefix, task_id):
    return '{0}:task:{1}'.format(app_prefix, task_id)


def get_pending_list_key(app_prefix, queue):
    return '{0}:{1}:pending'.format(app_prefix, queue)


def get_executing_list_key(app_prefix, queue):
    return '{0}:{1}:executing'.format(app_prefix, queue)


def get_results_channel_key(app_prefix):
    return '{0}:results'.format(app_prefix)


def get_worker_hash_key(app_prefix, worker_id):
    return '{0}:worker:{1}'.format(app_prefix, worker_id)
