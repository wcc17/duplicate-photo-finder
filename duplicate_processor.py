from multiprocessing import Process, Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_file_handler import DuplicateProcessorFileHandler
from hash_worker import HashWorker
from logger import Logger
from event_type import EventType
from duplicate_processor_event_handler import DuplicateProcessorEventHandler
from hash_event_handler import HashEventHandler
import os
import sys
import numpy

# TODO: either class name needs to change or the class needs to be split into two classes since it is handling the hash stuff now
class DuplicateProcessor:

    _output_directory_path = None
    _duplicates_folder_path = None
    _originals_folder_path = None
    _process_count = 0
    _verbose_logging = False
    _file_handler = None
    _logger = None
    _processor_event_handler = None
    _hash_event_handler = None

    _known_non_duplicates = []
    _known_duplicates = []
    _skipped_files = []

    def __init__(self, output_directory_path, duplicates_folder_path, originals_folder_path, process_count, verbose_logging):
        self._duplicates_folder_path = duplicates_folder_path
        self._originals_folder_path = originals_folder_path
        self._output_directory_path = output_directory_path
        self._process_count = process_count
        self._verbose_logging = verbose_logging

        self._logger = Logger()
        self._file_handler = DuplicateProcessorFileHandler(self._output_directory_path)
        self._processor_event_handler = DuplicateProcessorEventHandler()
        self._hash_event_handler = HashEventHandler()

    def execute(self):
        process_list = []
        hash_processor_event_queue = Queue()
        duplicate_processor_event_queue = Queue()

        try:
            potential_duplicate_filepaths = self._file_handler.get_filepaths(self._duplicates_folder_path, "duplicate folder")
            originals_folder_filepaths = self._file_handler.get_filepaths(self._originals_folder_path, "originals folder")
            
            self._file_handler.handle_processed_duplicates(potential_duplicate_filepaths, self._known_non_duplicates, self._known_duplicates, self._skipped_files)

            self._logger.print_log("hashing valid images from potential duplicates folder")
            sub_lists = self.__split_list_into_n_lists(potential_duplicate_filepaths, self._process_count)
            process_list = self.__setup_hash_processes(sub_lists, hash_processor_event_queue, True)
            potential_duplicate_image_models = self.__run_hash_processes(hash_processor_event_queue, len(potential_duplicate_filepaths), process_list, sub_lists)

            self._logger.print_log("hashing valid images from originals folder")
            sub_lists = self.__split_list_into_n_lists(originals_folder_filepaths, self._process_count)
            process_list = self.__setup_hash_processes(sub_lists, hash_processor_event_queue, False)
            originals_folder_image_models = self.__run_hash_processes(hash_processor_event_queue, len(originals_folder_filepaths), process_list, sub_lists)

            sub_lists = self.__split_list_into_n_lists(potential_duplicate_image_models, self._process_count)
            process_list = self.__setup_processor_processes(sub_lists, originals_folder_image_models, duplicate_processor_event_queue)
            
            already_processed = len(self._known_non_duplicates) + len(self._known_duplicates) + len(self._skipped_files)
            total_to_process = len(potential_duplicate_image_models) + already_processed

            self._logger.print_log("identifying duplicates")
            self.__run_processor_processes(duplicate_processor_event_queue, total_to_process, already_processed, process_list, sub_lists)
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

    # TODO: would like a way to make these two methods shorter, repeating a lot
    def __setup_hash_processes(self, potential_duplicate_sub_lists, event_queue, append_to_be_skipped):
        process_list  =[]

        process_id = 1
        for sub_list in potential_duplicate_sub_lists:
            process = Process(target=self.__execute_hash_worker, args=(sub_list, event_queue, process_id, append_to_be_skipped))
            process_list.insert(process_id-1, process)
            process_id += 1
        
        return process_list

    def __setup_processor_processes(self, potential_duplicate_sub_lists, originals_image_models, event_queue):
        process_list  =[]

        process_id = 1
        for sub_list in potential_duplicate_sub_lists:
            process = Process(target=self.__execute_processor_worker, args=(sub_list, originals_image_models, event_queue, process_id))
            process_list.insert(process_id-1, process)
            process_id += 1
        
        return process_list

    #TODO: need to combine these methods
    def __run_processor_processes(self, event_queue, total_to_process, already_processed, process_list, sub_lists):
        num_processed = already_processed
        process_num_processed_list = []
        process_num_processed_list = [0] * len(process_list)
        finished_process_count = 0

        if total_to_process > already_processed:
            for process in process_list:
                process.start()

            while True:
                event = None
                try:
                    event = event_queue.get(True, 1) 
                except:
                    pass

                if event is not None:
                    event_return_tuple = self._processor_event_handler.handle_event(event, process_num_processed_list, num_processed, self._known_duplicates, self._known_non_duplicates, self._skipped_files, total_to_process, sub_lists, process_list, finished_process_count)
                    num_processed = event_return_tuple[0]
                    finished_process_count = event_return_tuple[1]

                if finished_process_count >= len(process_list):
                    break

            for process in process_list:
                process.join()
        else:
            self._logger.print_log("No files found to compare")

    def __run_hash_processes(self, event_queue, total_to_process, process_list, sub_lists):
        num_processed = 0
        process_num_processed_list = []
        process_num_processed_list = [0] * len(process_list)
        finished_process_count = 0
        image_models = []

        if total_to_process > 0:
            for process in process_list:
                process.start()

            while True:
                event = None
                try:
                    event = event_queue.get(True, 1) 
                except:
                    pass

                if event is not None:
                    event_return_tuple = self._hash_event_handler.handle_event(event, num_processed, finished_process_count, image_models, self._skipped_files, process_num_processed_list, total_to_process, sub_lists, process_list)
                    num_processed = event_return_tuple[0]
                    finished_process_count = event_return_tuple[1]

                if finished_process_count >= len(process_list):
                    break

            for process in process_list:
                process.join()
        else:
            self._logger.print_log("No files found to hash")

        return image_models

    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        
        return False

    def __execute_processor_worker(self, duplicate_folder_image_models, originals_folder_image_models, queue, process_id):
        duplicate_processor_worker = DuplicateProcessorWorker(process_id, queue)
        duplicate_processor_worker.execute(duplicate_folder_image_models, originals_folder_image_models)

    def __execute_hash_worker(self, image_paths, queue, process_id, append_to_be_skipped):
        hash_worker = HashWorker(process_id, queue)
        hash_worker.execute(image_paths, append_to_be_skipped)

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