

def get_task_hash_key(queue, task_id):
    return '{0}:task:{1}'.format(queue, task_id)


def get_pending_list_key(queue):
    return '{0}:pending'.format(queue)


def get_executing_list_key(queue):
    return '{0}:executing'.format(queue)


def get_results_channel_key(queue):
    return '{0}:results'.format(queue)


def get_worker_hash_key(queue, worker_id):
    return '{0}:worker:{1}'.format(queue, worker_id)
