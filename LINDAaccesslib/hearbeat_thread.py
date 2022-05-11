"""
    **Contains the logic for KillableThread.**
"""
import threading


class KillableThread(threading.Thread):
    """
    Strats a thread which is always called until the user ordered to kill it.
    """
    def __init__(self, execut_func, sleep_interval=2):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.execut_func = execut_func

    def run(self):
        """
        Runs the loop.
        """
        while True:
            self.execut_func()
            # If no kill signal is set, sleep for the interval,
            # If kill signal comes in while sleeping, immediately
            #  wake up and handle
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break

        print("Killing Thread")

    def kill(self):
        self._kill.set()
