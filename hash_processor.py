from processor_file_handler import ProcessorFileHandler
from base_processor import BaseProcessor
from hash_event_handler import HashEventHandler
from hash_worker import HashWorker

class HashProcessor(BaseProcessor):

    _hash_event_handler = None
    _use_verbose_logging = False
    _should_check_videos = False

    def __init__(self, file_handler, use_verbose_logging, should_check_videos):
        super().__init__(file_handler)
        self._hash_event_handler = HashEventHandler(use_verbose_logging)
        self._use_verbose_logging = use_verbose_logging
        self._should_check_videos = should_check_videos

    def process(self, process_count, folder_path, folder_name, skipped_files, append_to_skipped):
        self._process_list = []
        image_models = []

        filepaths = self._file_handler.get_filepaths(folder_path, folder_name)
        num_filepaths = len(filepaths)

        self._logger.print_log("Number of files found in " + folder_name + " to attempt to md5 hash: " + str(num_filepaths) + ". Starting hash process. ")
        self._sub_lists = self._split_list_into_n_lists(filepaths, process_count)
        self._two_way_connections = self._setup_connections(process_count)

        self._setup_processes()
        self._run_processes(len(filepaths), self._hash_event_handler.handle_event, (image_models, skipped_files, append_to_skipped))

        self._logger.print_log("Hashed " + str(len(image_models)) + " media files" + " and skipped " + str(num_filepaths - len(image_models)) + ". ")
        return image_models

    def _setup_processes(self):
        process_id = 1
        for sub_list in self._sub_lists:
            process = HashWorker(process_id, self._event_queue, sub_list, self._use_verbose_logging, self._should_check_videos, self._two_way_connections[process_id-1].child_connection)
            
            self._process_list.insert(process_id-1, process)
            process_id += 1

        self._process_num_processed_list = [0] * len(self._process_list)

    def _replace_process(self, process, sub_list):
        new_process = HashWorker(process.process_id, self._event_queue, sub_list, self._use_verbose_logging, self._should_check_videos, self._two_way_connections[process.process_id-1].child_connection)
        return new_process