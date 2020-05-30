from multiprocessing import Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_event_handler import DuplicateProcessorEventHandler
from base_processor import BaseProcessor
import os
import sys

class DuplicateProcessor(BaseProcessor):

    _processor_event_handler = None
    _file_handler = None

    def __init__(self, file_handler, use_verbose_logging):
        super().__init__(file_handler)
        self._processor_event_handler = DuplicateProcessorEventHandler(use_verbose_logging)

    def process(self, process_count, potential_duplicate_image_models, originals_folder_image_models, known_non_duplicates, known_duplicates, skipped_files, single_folder_dupe_search):

        sub_lists = self._split_list_into_n_lists(potential_duplicate_image_models, process_count)
        self._setup_processes(self.__execute_processor_worker, originals_folder_image_models, sub_lists)
        
        already_processed = len(known_non_duplicates) + len(known_duplicates) + len(skipped_files)
        total_to_process = len(potential_duplicate_image_models) + already_processed

        self._logger.print_log("identifying duplicates")
        self._run_processes(total_to_process, self._processor_event_handler.handle_event, (sub_lists, known_duplicates, known_non_duplicates, skipped_files, single_folder_dupe_search))
        self._file_handler.write_output_for_files(known_non_duplicates, known_duplicates, skipped_files)

    def __execute_processor_worker(self, process_id, queue, originals_folder_image_models, duplicate_folder_image_models):
        duplicate_processor_worker = DuplicateProcessorWorker(process_id, queue)
        duplicate_processor_worker.execute(duplicate_folder_image_models, originals_folder_image_models)