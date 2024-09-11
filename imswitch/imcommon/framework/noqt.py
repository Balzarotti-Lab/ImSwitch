from abc import ABCMeta
import psygnal
import imswitch.imcommon.framework.base as base
import threading 
import queue 

class Mutex(base.Mutex):
    def __init__(self):
        self._lock = threading.Lock()

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def try_lock(self):
        return self._lock.acquire(blocking=False)


class Signal(base.Signal):
    def __new__(cls, *argtypes) -> base.Signal:
        # psygnal.Signal does not take argument types in the same way
        return psygnal.Signal(argtypes)

class SignalInterface(base.SignalInterface):
    # Implement alternative SignalInterface functionality if needed
    pass


class Thread(threading.Thread, base.Thread): #TODO: @jacopoabramo -> Fix this by adding, base.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self.isRunning = False

    def run(self):
        self.isRunning = True
        while not self._stop_event.is_set():
            if self._target:
                self._target()
                break  
        self.isRunning = False

    def quit(self, timeout=None) -> None:
        self._stop_event.set()

    def wait(self, timeout=None) -> None:
        self.join(timeout)

    
    def finished(self) -> bool:
        return not self.isRunning
    
    def started(self) -> bool:
        return self.isRunning
    
class Timer(base.Timer):
    def __init__(self, interval, function, args=None, kwargs=None):
        super().__init__()
        self._timer = threading.Timer(interval, function, args=args, kwargs=kwargs)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()

class Worker(base.Worker):
    def __init__(self, target=None):
        super().__init__()
        self._thread = threading.Thread(target=self._run)
        self._task_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._target = target

    def _run(self):
        while not self._stop_event.is_set():
            try:
                task = self._task_queue.get(timeout=0.1)  # adjust timeout as needed
                if task is None:
                    break
                task()
            except queue.Empty:
                continue

        if self._target:
            self._target()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._task_queue.put(None)
        self._thread.join()

    def move_to_thread(self, func):
        self._task_queue.put(func)
