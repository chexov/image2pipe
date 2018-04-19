from multiprocessing import queues


def yield_from_queue(q, timeout_sec=0.42):
    """
    Checks queue for new item and yields it
    If item is None then it is end of cycle

    :type timeout_sec: float
    :type q: queues.Queue
    """
    while True:
        try:
            x = q.get(True, timeout_sec)
            if x is None:
                break
            yield x
        except queues.Empty:
            pass
