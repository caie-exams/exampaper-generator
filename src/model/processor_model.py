import threading
import queue


class ProcessorModel(threading.Thread):
    """
    model of subclass multithreading processor

    child class will only need to overwrite
    the _process(task) method for it to work
    """

    def __init__(self, done_list=None):
        """
        if done_list is not None, the result of tasks
        will be appended to the back of done list 
        """
        super(ProcessorModel, self).__init__()
        self._done_list = done_list
        # threading related
        self._active = threading.Event()  # task pending
        self._alive = threading.Event()  # is terminating
        self._alive.set()

        # not threading related
        self._task_queue = queue.Queue()

    def run(self):
        while (not self._task_queue.empty()) \
                or self._alive.is_set():
            self._active.wait()
            # process tasks
            if not self._task_queue.empty():
                task = self._task_queue.get()
                result = self._process(task)
                if self._done_list is not None:
                    self._done_list.extend(result)
            else:
                self._active.clear()
        self._active.clear()
        self._alive.clear()

    def _process(self, task):
        pass

    def stop(self):
        """
        stops the processor

        note that the processor will finish all 
        pending job before fully terminated
        """
        self._active.set()
        self._alive.clear()

    def status(self):
        """
        returns the state of processor

        True - True:    running and busy   
        True - False:   running and ideal   
        False - True:   terminating and busy   
        False - False:  terninated   
        """
        return self._alive.is_set(), self._active.is_set(), self._task_queue.qsize()

    def add_task(self, task):
        """
        add new task to the task queue 

        if the processor is terminating and
        a new task is addded, raise an error
        """
        if not self._alive.is_set():
            raise Exception("new task can't be added while terminating")
        self._task_queue.put(task)
        self._active.set()
