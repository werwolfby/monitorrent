from builtins import object

import sys
import threading



def timer(interval, timer_func, *args, **kwargs):
    stopped = threading.Event()
    def loop_fn():
        while not stopped.wait(interval):
            timer_func(*args, **kwargs)
    threading.Thread(target=loop_fn).start()    
    return stopped.set
