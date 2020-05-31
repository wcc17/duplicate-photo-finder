from processor_file_handler import ProcessorFileHandler
from base_processor import BaseProcessor
from hash_event_handler import HashEventHandler
from hash_worker import HashWorker

class HashProcessor(BaseProcessor):

    _hash_event_handler = None

    def __init__(self, file_handler, use_verbose_logging):
        super().__init__(file_handler)
        self._hash_event_handler = HashEventHandler(use_verbose_logging)

    def process(self, process_count, folder_path, folder_name, known_non_duplicates, known_duplicates, skipped_files, append_to_skipped):
        self._process_list = []
        image_models = []

        filepaths = self._file_handler.get_filepaths(folder_path, folder_name)
        
        self._logger.print_log("hashing valid media files from " + folder_name)
        sub_lists = self._split_list_into_n_lists(filepaths, process_count)
        
        self._setup_processes(sub_lists)
        self._run_processes(len(filepaths), self._hash_event_handler.handle_event, (image_models, skipped_files, sub_lists, append_to_skipped))

        self._logger.print_log("hashed " + str(len(image_models)) + " media files and skipped: " + str(len(skipped_files)))
        return image_models

    def _setup_processes(self, sub_lists):
        process_id = 1
        for sub_list in sub_lists:
            process = HashWorker(process_id, self._event_queue, sub_list)
            self._process_list.insert(process_id-1, process)
            process_id += 1