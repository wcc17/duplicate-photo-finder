from multiprocessing import Queue
from logger import Logger
from multiprocessing import Process
import numpy

class BaseProcessor:

    _logger = None
    _file_handler = None
    _process_list = []
    _event_queue = None

    def __init__(self, file_handler):
        self._logger = Logger()
        self._file_handler = file_handler
        self._event_queue = Queue()

    def kill_processes(self):
        self.__kill_processes(self._process_list)

    def _split_list_into_n_lists(self, list, number_of_lists):
        #TODO: I would prefer to not use numpy for this if possible
        sub_lists = numpy.array_split(numpy.array(list), number_of_lists)
        sub_lists = numpy.array(sub_lists).tolist()
        return sub_lists

    def _setup_processes(self, target_func, additional_execution_args, sub_lists):
        process_id = 1
        for sub_list in sub_lists:
            args_to_use = (process_id, self._event_queue) # TODO: this is a hack and wouldn't be necessary if workers subclassed Process

            if not additional_execution_args == None:
                if isinstance(additional_execution_args, tuple):
                    args_to_use += additional_execution_args
                else:
                    args_to_use += (additional_execution_args,)

            args_to_use += (sub_list,)

            process = Process(target=target_func, args=args_to_use)
            self._process_list.insert(process_id-1, process)
            process_id += 1

    def __kill_processes(self, process_list):
        self._logger.print_log("Terminating all processes")
        for process in process_list:
            process.terminate()
            process.join()
        self._process_list = []
        self._logger.print_log("Terminated " + str(len(process_list)) + " processes")

    def _run_processes(self, total_to_process, event_handler_func, event_handler_args):
        num_processed = 0
        process_num_processed_list = []
        process_num_processed_list = [0] * len(self._process_list)
        finished_process_count = 0

        for process in self._process_list:
            process.start()

        while True:
            event = None
            try:
                event = self._event_queue.get(True, 1) 
            except:
                pass

            if event is not None:
                #TODO: i want to stop doing this with the arguments its awful
                args_to_use = (event, num_processed, process_num_processed_list, finished_process_count, total_to_process, self._process_list)
                args_to_use += event_handler_args


                event_return_tuple = event_handler_func(*args_to_use)

                num_processed = event_return_tuple[0]
                finished_process_count = event_return_tuple[1]

            if finished_process_count >= len(self._process_list):
                break

        for process in self._process_list:
            process.join()

    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        
        return False