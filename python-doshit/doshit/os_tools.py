import resource


def set_virtual_memory_limit(limit_in_bytes):
    """
    sets the virtual memory limit for the current process.
    :param limit_in_bytes:
    """
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)

    if hard > 0:
        soft = min(limit_in_bytes, hard)
    else:
        soft = limit_in_bytes

    resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)

    print 'virtual memory limit changed to:', soft
