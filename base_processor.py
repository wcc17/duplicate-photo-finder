from multiprocessing import Queue, Manager
from logger import Logger
from multiprocessing import Process
from one_way_connection import OneWayConnection
from num_processed_model import NumProcessedModel
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
    _sub_lists = []
    _manager = None
    _use_verbose_logging = None
    _enable_redisperse = False
    
    def __init__(self, file_handler, use_verbose_logging, enable_redisperse):
        self._logger = Logger()
        self._file_handler = file_handler
        self._event_queue = Queue()
        self._manager = Manager()
        self._use_verbose_logging = use_verbose_logging
        self._enable_redisperse = enable_redisperse

    def kill_processes(self):
        self._logger.print_log("Terminating all processes")
        for process in self._process_list:
            process.terminate()
            process.join()
        self._process_list = []
        self._logger.print_log("Terminated " + str(len(self._process_list)) + " processes")

    def setup_connections(self, process_count):
        self._one_way_connections = []
        for i in range(0, process_count):
            self._one_way_connections.append(OneWayConnection())

    def _initialize_managed_sublists(self, list, number_of_lists):
        self._sub_lists = []

        sub_lists_array = numpy.array_split(numpy.array(list), number_of_lists)
        sub_lists_list = numpy.array(sub_lists_array).tolist()

        for i in range(0, len(sub_lists_list)):
            sub_lists_list[i] = self._manager.list(sub_lists_list[i])

        self._sub_lists = sub_lists_list

    def _run_processes(self, total_to_process, event_handler_func, event_handler_args):
        continue_processing = True

        self._setup_processes()
        self.__setup_processed_counts()
        self.__start_processes()

        while continue_processing:
            if self._enable_redisperse and self._should_redisperse:
                self.__redisperse(total_to_process, event_handler_func, event_handler_args)
            else:
                continue_processing = self.__process(total_to_process, event_handler_func, event_handler_args)

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
            args_to_use = (event, self._num_processed, self._process_num_processed_list, self._finished_process_count, total_to_process, self._process_list)
            args_to_use += event_handler_args

            event_return_tuple = event_handler_func(*args_to_use)

            self._num_processed = event_return_tuple[0]
            self._finished_process_count = event_return_tuple[1]

    def __start_redisperse_if_applicable(self, total_to_process):
        if self._enable_redisperse:
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
            self.__cleanup_connections()

            #create new processes and restart
            self._should_redisperse = False
            self._finished_process_count = 0 
            self.setup_connections(len(self._sub_lists))
            self.__reset_processes(files_to_be_processed)
            self.__reset_num_processed_models()
            self.__start_processes()

    def __gather_existing_sub_lists(self):
        files_to_be_processed = []
        for sub_list in self._sub_lists:
            files_to_be_processed.extend(sub_list)

        return files_to_be_processed

    def __reset_processes(self, files_to_be_processed):
        self._initialize_managed_sublists(files_to_be_processed, len(self._process_list))
        for i in range(0, len(self._process_list)):
            self._process_list[i] = self._replace_process(self._process_list[i])

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
            sending_connection =  self._one_way_connections[process_id].sending_connection
            sending_connection.send("REDISPERSE")
            self._logger.print_log("sent the redisperse message")

    def __setup_processed_counts(self):
        self._process_num_processed_list = []

        for sub_list in self._sub_lists:
            num_processed_model = NumProcessedModel(0, len(sub_list))
            self._process_num_processed_list.append(num_processed_model)

    def __reset_num_processed_models(self):
        for i in range(0, len(self._sub_lists)):
            num_processed_model = self._process_num_processed_list[i]
            new_sub_list = self._sub_lists[i]

            num_processed_model = NumProcessedModel(num_processed_model.num_processed, (num_processed_model.num_processed + len(new_sub_list)))
            self._process_num_processed_list[i] = num_processed_model

            #the new total to process should be num_processed + new_total
            # process1: 1 / 10
            # process2: 9 / 10
            # process3: 10 / 10
            # process4: 5 / 10

            #9 + 1 + 5 remaining = 15 remaining
            #4, 4, 4, 3 is the new distribution

            # process1: 1 / (1 + 4) == 1 / 5
            # process2: 9 / (9 + 4) == 9 / 13
            # process3: 10 / (10 + 4) == 10 / 14
            # process4: 5 / (5 + 3) == 5 / 8

            # 5 + 13 + 14 + 8 == 40

    def __cleanup(self):
        for process in self._process_list:
            process.terminate()

        for process in self._process_list:
            process.join()

        self.__cleanup_connections()

        self._event_queue.close()
        self._event_queue.join_thread()
        self._process_list = []
        self._process_num_processed_list = []
        self._sub_lists = []

    def __cleanup_connections(self):
        for connection in self._one_way_connections:
            connection.receiving_connection.close()
            connection.sending_connection.close()

        self._one_way_connections = []

    def _replace_process(self, process):
        raise AttributeError("_replace_process should be overriden outside of BaseProcessor")

    def _setup_processes(self):
        raise AttributeError("_setup_processes should be overriden outside of BaseProcessor")
    