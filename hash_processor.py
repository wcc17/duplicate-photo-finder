from processor_file_handler import ProcessorFileHandler
from base_processor import BaseProcessor
from hash_event_handler import HashEventHandler
from hash_worker import HashWorker

class HashProcessor(BaseProcessor):

    _hash_event_handler = None

    def __init__(self, file_handler, use_verbose_logging):
        super().__init__(file_handler)
        self._hash_event_handler = HashEventHandler(use_verbose_logging)

    def process(self, process_count, folder_path, folder_name, known_non_duplicates, known_duplicates, skipped_files, process_existing_duplicates, append_to_skipped):
        self._process_list = []
        image_models = []

        filepaths = self._file_handler.get_filepaths(folder_path, folder_name)
        
        if process_existing_duplicates:
            self.__process_existing_duplicates(filepaths, known_non_duplicates, known_duplicates, skipped_files)

        self._logger.print_log("hashing valid media files from " + folder_name)
        sub_lists = self._split_list_into_n_lists(filepaths, process_count)
        
        self._setup_processes(self.__execute_hash_worker, None, sub_lists)
        self._run_processes(len(filepaths), self._hash_event_handler.handle_event, (image_models, skipped_files, sub_lists, append_to_skipped))

        self._logger.print_log("hashed " + len(image_models) + " media files and skipped: " + len(skipped_files))
        return image_models

    def __process_existing_duplicates(self, filepaths, known_non_duplicates, known_duplicates, skipped_files):
        self._logger.print_log("sort out duplicates files that have already been marked as processed...")
        self._file_handler.handle_processed_duplicates(filepaths, known_non_duplicates, known_duplicates, skipped_files)
        self._logger.print_log("duplicate folder files count after scanning for already processed: " + str(len(filepaths)))

    def __execute_hash_worker(self, process_id, queue, image_paths):
        hash_worker = HashWorker(process_id, queue)
        hash_worker.execute(image_paths)