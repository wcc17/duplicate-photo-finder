import sys
from multiprocessing import Queue, Manager, Process
from logger import Logger

class BaseProcessor:

    _logger = None
    _file_handler = None
    _process_list = []
    _manager = None
    _event_queue = None
    _task_queue = None
    _process_count = 0
    _use_verbose_logging = False

    def __init__(self, file_handler, process_count, use_verbose_logging):
        self._file_handler = file_handler
        self._process_count = process_count
        self._use_verbose_logging = use_verbose_logging
        
        self._logger = Logger()
        self._manager = Manager()
        self._event_queue = self._manager.Queue()
        self._task_queue = self._manager.Queue()

    def _get_process(self, process_id):
        raise AttributeError("not supported")

    def _run_processes(self, items_to_process, event_handler_func, event_handler_args):
        total_to_process = len(items_to_process)

        processes = self._initialize_processes()
        self._fill_task_queue(items_to_process)

        self._process_events(total_to_process, event_handler_func, event_handler_args)

        self._stop_processes(processes)

    def _initialize_processes(self):
        processes = []
        for i in range(self._process_count):
            process = self._get_process(i)
            processes.append(process)
            process.start()

        return processes

    def _fill_task_queue(self, items):
        for item in items:
            self._task_queue.put(item)

    def _process_events(self, total_to_process, event_handler_func, event_handler_args):
        num_processed = 0
        num_processed_by_process_list = [0] * self._process_count
        
        while True:
            self._write_progress_to_console(num_processed, total_to_process, num_processed_by_process_list)

            event = None
            try:
                event = self._event_queue.get(True, 1) 
            except:
                pass

            if event is not None:
                args_to_use = (event, num_processed_by_process_list, num_processed, total_to_process)
                args_to_use += event_handler_args

                num_processed = event_handler_func(*args_to_use)

            if num_processed >= total_to_process:
                break

    def _stop_processes(self, processes):
        for i in range(self._process_count):
            self._task_queue.put(-1)

        for process in processes:
            process.join()

    def _write_progress_to_console(self, num_processed, total_to_process, num_processed_by_process_list):
        output_str = "Progress: " + str(num_processed) + "/" + str(total_to_process) + "        "

        for i in range(len(num_processed_by_process_list)):
            output_str += ("P" + str(i) + ": " + str(num_processed_by_process_list[i]) + "  ")

        sys.stdout.write(output_str + "\r")
        sys.stdout.flush()

    def _log_process_message(self, process_id, message):
        if self._use_verbose_logging:
            self._logger.print_log("[process: " + str(process_id) + "] " + message)