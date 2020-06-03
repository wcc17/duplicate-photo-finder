from multiprocessing import Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_event_handler import DuplicateProcessorEventHandler
from base_processor import BaseProcessor
import os
import sys

class DuplicateProcessor(BaseProcessor):

    _processor_event_handler = None
    _file_handler = None

    def __init__(self, file_handler, use_verbose_logging, process_count):
        super().__init__(file_handler, process_count)
        self._processor_event_handler = DuplicateProcessorEventHandler(use_verbose_logging)

    def process(self, potential_duplicate_image_models, originals_folder_image_models, known_non_duplicates, known_duplicates, skipped_files, single_folder_dupe_search):

        # process = DuplicateProcessorWorker(process_id, self._event_queue, sub_list, originals_folder_image_models)
        
        total_to_process = len(potential_duplicate_image_models)

        self._logger.print_log("identifying duplicates, progress will not include skipped files")
        self._run_processes(total_to_process, self._processor_event_handler.handle_event, (known_duplicates, known_non_duplicates, skipped_files, single_folder_dupe_search))
        self._file_handler.write_output_for_files(known_non_duplicates, known_duplicates, skipped_files)