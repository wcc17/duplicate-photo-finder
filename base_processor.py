from multiprocessing import Queue
from logger import Logger
from multiprocessing import Process
from two_way_connection import TwoWayConnection
from enum import Enum
import numpy


class BaseProcessor:

    _logger = None
    _file_handler = None
    _process_list = []
    _event_queue = None
    _num_processed = 0
    _finished_process_count = 0
    _should_redisperse = False
    _process_num_processed_list = []
    _parent_connections = []
    _two_way_connections = []

    def __init__(self, file_handler):
        self._logger = Logger()
        self._file_handler = file_handler
        self._event_queue = Queue()

    def kill_processes(self):
        self._logger.print_log("Terminating all processes")
        for process in self._process_list:
            process.terminate()
            process.join()
        self._process_list = []
        self._logger.print_log("Terminated " + str(len(self._process_list)) + " processes")

    def _split_list_into_n_lists(self, list, number_of_lists):
        sub_lists = numpy.array_split(numpy.array(list), number_of_lists)
        sub_lists = numpy.array(sub_lists).tolist()
        return sub_lists

    def _setup_connections(self, process_count):
        connections = []
        for i in range(0, process_count):
            connection = TwoWayConnection()
            connections.append(connection)

        return connections

    def _run_processes(self, total_to_process, event_handler_func, event_handler_args):
        continue_processing = True
        self.__setup_parent_connections()
        self.__start_processes()

        while continue_processing:
            continue_processing = self.__process(total_to_process, event_handler_func, event_handler_args)
            if(self._should_redisperse):
                self.__redisperse()

        self.__cleanup()

    def __process(self, total_to_process, event_handler_func, event_handler_args):

        event = None
        try:
            event = self._event_queue.get(True, 1) # TODO: I wonder how often this 1 second is used? is it necessary? is it delaying anything?
        except:
            pass

        if event is not None:
            args_to_use = (event, self._num_processed, self._process_num_processed_list, self._finished_process_count, total_to_process, self._process_list)
            args_to_use += event_handler_args

            event_return_tuple = event_handler_func(*args_to_use)

            self._num_processed = event_return_tuple[0]
            self._finished_process_count = event_return_tuple[1]

        if self._finished_process_count >= len(self._process_list):
            return False

        if self._finished_process_count > 0:

            minimum_to_trigger_redispurse = len(self._process_list)

            if (total_to_process - self._num_processed) >= minimum_to_trigger_redispurse:
                print()
                self._logger.print_log("Redispersing " + str(total_to_process - self._num_processed) + " to account for process that finished before others")
                self._should_redisperse = True
                self.__ask_processes_to_stop_for_redisperse()

                for process in self._process_list:
                    process.join()
            return True

        return True

    def __redisperse(self):
        if not self.__some_process_is_alive():
            files_to_be_processed = []
            for process in self._process_list:
                process_file_list = self._parent_connections[process.process_id-1].recv()
                files_to_be_processed.extend(process_file_list)

            sub_lists = self._split_list_into_n_lists(files_to_be_processed, len(self._process_list))
            for i in range(0, len(self._process_list)):
                self._process_list[i] = self._replace_process(self._process_list[i], sub_lists[i])
                self._process_num_processed_list[i] = 0

            self.__start_processes()
            self._finished_process_count = 0 
            self._should_redisperse = False

    def _replace_process(self, process, sub_list):
        return ""

    def __setup_parent_connections(self):
        for connection in self._two_way_connections:
            self._parent_connections.append(connection.parent_connection)

    def __start_processes(self):
        for process in self._process_list:
            process.start()

    def __some_process_is_alive(self):
        for process in self._process_list:
            if process.is_alive():
                return True
        
        return False

    def __ask_processes_to_stop_for_redisperse(self):
        for process_id in range(0, len(self._process_list)):
            self._parent_connections[process_id].send("REDISPERSE")

    def __cleanup(self):
        for process in self._process_list:
            process.join()

        for process in self._process_list:
            process.terminate()

        for connection in self._two_way_connections:
            connection.parent_connection.close()
            connection.child_connection.close()

        self._event_queue.close()
        self._event_queue.join_thread()