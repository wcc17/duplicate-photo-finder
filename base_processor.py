from multiprocessing import Queue, Pool, Manager, Process
from logger import Logger

class BaseProcessor:

    _logger = None
    _file_handler = None
    _process_list = []
    _manager = None
    _event_queue = None
    _task_queue = None
    _process_count = 0

    def __init__(self, file_handler, process_count):
        self._file_handler = file_handler
        self._process_count = process_count
        
        self._logger = Logger()
        self._manager = Manager()
        self._event_queue = self._manager.Queue()
        self._task_queue = self._manager.Queue()

    def _get_process(self, process_id):
        raise AttributeError("not supported")

    def _run_processes(self, filepaths, event_handler_func, event_handler_args):
        num_processed = 0
        total_to_process = len(filepaths)

        processes = []
        for i in range(self._process_count):
            process = self._get_process(i)
            processes.append(process)
            process.start()

        for filepath in filepaths:
            self._task_queue.put(filepath)

        while True:
            event = None
            try:
                event = self._event_queue.get(True, 1) 
            except:
                pass

            if event is not None:
                args_to_use = (event, num_processed, total_to_process)
                args_to_use += event_handler_args

                num_processed = event_handler_func(*args_to_use)

            if num_processed >= total_to_process:
                break

        for i in range(self._process_count * 2):
            self._task_queue.put(-1)

        for process in processes:
            process.join()