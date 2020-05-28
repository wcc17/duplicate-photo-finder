from multiprocessing import Process, Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_file_handler import DuplicateProcessorFileHandler
from logger import Logger
from event_type import EventType
from duplicate_processor_event_handler import DuplicateProcessorEventHandler
import os
import sys
import numpy

class DuplicateProcessor:

    _output_directory_path = None
    _duplicates_folder_path = None
    _originals_folder_path = None
    _rescan_for_duplicates = False
    _omit_known_duplicates = False
    _process_count = 0
    _file_handler = None
    _logger = None
    _event_handler = None

    _known_non_duplicates = []
    _known_duplicates = []
    _skipped_files = []

    def __init__(self, output_directory_path, duplicates_folder_path, originals_folder_path, process_count):
        self._duplicates_folder_path = duplicates_folder_path
        self._originals_folder_path = originals_folder_path
        self._output_directory_path = output_directory_path
        self._process_count = process_count

        self._logger = Logger()
        self._file_handler = DuplicateProcessorFileHandler(self._output_directory_path)
        self._event_handler = DuplicateProcessorEventHandler()

    def execute(self):
        process_list = []
        event_queue = Queue()

        try:
            self._logger.print_log("backup old output files before writing output to file again...")

            potential_duplicate_image_models = self._file_handler.get_possible_duplicates_image_models(self._duplicates_folder_path, "duplicate folder")
            originals_folder_image_models = self._file_handler.get_originals_image_models(self._originals_folder_path, "originals folder")
            
            self.__get_already_processed_file_info()
            self._file_handler.backup_old_output_files()

            potential_duplicate_sub_lists = self.__split_list_into_n_lists(potential_duplicate_image_models, self._process_count)
            process_list = self.__setup_processes(potential_duplicate_sub_lists, originals_folder_image_models, event_queue)
            
            already_processed = len(self._known_non_duplicates) + len(self._known_duplicates) + len(self._skipped_files)
            total_to_process = len(potential_duplicate_image_models) + already_processed

            self.__run_processes(event_queue, total_to_process, already_processed, process_list, potential_duplicate_sub_lists)
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._skipped_files)

        except KeyboardInterrupt:
            self._logger.print_log('Interrupted, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._skipped_files)
            self.__kill_processes(process_list)
            raise
        except Exception:
            self._logger.print_log('Exception occurred, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._skipped_files)
            self.__kill_processes(process_list)
            raise

    def __setup_processes(self, potential_duplicate_sub_lists, originals_image_models, event_queue):
        process_list  =[]

        process_id = 1
        for sub_list in potential_duplicate_sub_lists:
            process = Process(target=self.__execute_worker, args=(sub_list, originals_image_models, event_queue, process_id))
            process_list.insert(process_id-1, process)
            process_id += 1
        
        return process_list

    def __run_processes(self, event_queue, total_to_process, already_processed, process_list, sub_lists):
        num_processed = already_processed
        process_num_processed_list = []
        process_num_processed_list = [None] * len(process_list)
        finished_process_count = 0

        for process in process_list:
            process.start()

        while True:
            try:
                event = event_queue.get(True, 1) 
                event_return_tuple = self._event_handler.handle_event(event, process_num_processed_list, num_processed, self._known_duplicates, self._known_non_duplicates, self._skipped_files, total_to_process, sub_lists, process_list, finished_process_count)

                num_processed = event_return_tuple[0]
                finished_process_count = event_return_tuple[1]
            except:
                pass

            if finished_process_count >= len(process_list):
                break

        for process in process_list:
            process.join()

    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        
        return False

    def __execute_worker(self, duplicate_folder_image_models, originals_folder_image_models, queue, process_id):
        duplicate_processor_worker = DuplicateProcessorWorker(process_id, queue)
        duplicate_processor_worker.execute(duplicate_folder_image_models, originals_folder_image_models)

    def __split_list_into_n_lists(self, list, number_of_lists):
        #TODO: I would prefer to not use numpy for this if possible
        sub_lists = numpy.array_split(numpy.array(list), number_of_lists)
        sub_lists = numpy.array(sub_lists).tolist()
        return sub_lists

    def __kill_processes(self, process_list):
        self._logger.print_log("Terminating all processes")
        for process in process_list:
            process.terminate()
            process.join()
        self._logger.print_log("Terminated " + str(len(process_list)) + " processes")

    def __get_already_processed_file_info(self):
        already_processed_tuple = self._file_handler.get_already_processed_file_info()
        self._known_non_duplicates = already_processed_tuple[0] 
        self._known_duplicates = already_processed_tuple[1] 
        self._skipped_files = already_processed_tuple[2]