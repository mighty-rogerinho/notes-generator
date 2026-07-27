import itertools
import sys
import time
import threading

def spinner(done_event, msg="Processing"):
    """Call this in a thread while doing a long task"""
    for c in itertools.cycle("|/-\\"):
        if done_event.is_set():
            break
        sys.stdout.write(f"\r{msg}... {c}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(msg) + 5) + "\r")