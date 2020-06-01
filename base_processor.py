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
    _two_way_connections = []
    _sub_lists = []

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
        self._two_way_connections = []
        for i in range(0, process_count):
            connection = TwoWayConnection()
            self._two_way_connections.append(connection)

    def _run_processes(self, total_to_process, event_handler_func, event_handler_args):
        continue_processing = True
        self.__start_processes()

        while continue_processing:
            continue_processing = self.__process(total_to_process, event_handler_func, event_handler_args)
            if(self._should_redisperse):
                self.__redisperse(total_to_process, event_handler_func, event_handler_args)

        self.__cleanup()

    def __process(self, total_to_process, event_handler_func, event_handler_args):

        self.__process_event(total_to_process, event_handler_func, event_handler_args)

        if self._finished_process_count >= len(self._process_list):
            return False

        if self._finished_process_count > 0:
            self.__start_redisperse_if_applicable(total_to_process)
            
            return True

        return True

    def __process_event(self, total_to_process, event_handler_func, event_handler_args):
        event = None
        try:
            event = self._event_queue.get(True, 1) # TODO: I wonder how often this 1 second is used? is it necessary? is it delaying anything?
        except:
            pass

        if event is not None:
            args_to_use = (event, self._num_processed, self._process_num_processed_list, self._finished_process_count, total_to_process, self._process_list, self._sub_lists)
            args_to_use += event_handler_args

            event_return_tuple = event_handler_func(*args_to_use)

            self._num_processed = event_return_tuple[0]
            self._finished_process_count = event_return_tuple[1]

    def __start_redisperse_if_applicable(self, total_to_process):
        minimum_to_trigger_redispurse = len(self._process_list) * 4

        if (total_to_process - self._num_processed) >= minimum_to_trigger_redispurse:
            self._should_redisperse = True
            self.__ask_processes_to_stop_for_redisperse()

    def __redisperse(self, total_to_process, event_handler_func, event_handler_args):
        if not self.__some_process_is_alive():
            #get the rest of the events out the queue
            while not self._event_queue.empty():
                self.__process_event(total_to_process, event_handler_func, event_handler_args)

            self._logger.print_log("Redispersing " + str(total_to_process - self._num_processed) + " to account for process that finished before others")

            #get the shortened sub lists from all the processes to be redispersed
            files_to_be_processed = self.__gather_existing_sub_lists()

            #cleanup and then create new connections for the new processes
            self.__cleanup_connections()
            self._setup_connections(len(self._process_list))
            
            #create new processes and restart
            self.__reset_processes(files_to_be_processed)
            self.__start_processes()
            self._finished_process_count = 0 
            self._should_redisperse = False

    def __gather_existing_sub_lists(self):
        files_to_be_processed = []
        for process in self._process_list:
            conn = self._two_way_connections[process.process_id-1].parent_connection
            process_file_list = conn.recv()
            files_to_be_processed.extend(process_file_list)

        return files_to_be_processed

    def __reset_processes(self, files_to_be_processed):
        self._sub_lists = self._split_list_into_n_lists(files_to_be_processed, len(self._process_list))
        for i in range(0, len(self._process_list)):
            self._process_list[i] = self._replace_process(self._process_list[i], self._sub_lists[i])
            self._process_num_processed_list[i] = 0

    def _replace_process(self, process, sub_list):
        return ""

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
            parent_connection =  self._two_way_connections[process_id].parent_connection
            parent_connection.send("REDISPERSE")

    def __cleanup(self):
        for process in self._process_list:
            process.terminate()

        for process in self._process_list:
            process.join()

        self.__cleanup_connections()

        self._event_queue.close()
        self._event_queue.join_thread()

    def __cleanup_connections(self):
        for connection in self._two_way_connections:
            connection.parent_connection.close()
            connection.child_connection.close()