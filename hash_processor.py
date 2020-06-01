from processor_file_handler import ProcessorFileHandler
from base_processor import BaseProcessor
from hash_event_handler import HashEventHandler
from hash_worker import HashWorker

class HashProcessor(BaseProcessor):

    _hash_event_handler = None
    _should_check_videos = False

    def __init__(self, file_handler, use_verbose_logging, should_check_videos, enable_redisperse):
        super().__init__(file_handler, use_verbose_logging, enable_redisperse)
        self._hash_event_handler = HashEventHandler(use_verbose_logging)
        self._should_check_videos = should_check_videos

    def process(self, process_count, folder_path, folder_name, skipped_files, append_to_skipped):
        self._process_list = []
        image_models = []

        filepaths = self._file_handler.get_filepaths(folder_path, folder_name)
        num_filepaths = len(filepaths)

        self._logger.print_log("Number of files found in " + folder_name + " to attempt to md5 hash: " + str(num_filepaths) + ". Starting hash process. ")
        self._initialize_managed_sublists(filepaths, process_count)

        self._setup_processes()
        self._run_processes(len(filepaths), self._hash_event_handler.handle_event, (image_models, skipped_files, append_to_skipped))

        self._logger.print_log("Hashed " + str(len(image_models)) + " media files" + " and skipped " + str(num_filepaths - len(image_models)) + ". ")
        return image_models

    def _setup_processes(self):
        self.setup_connections(len(self._sub_lists))

        process_id = 1
        for sub_list in self._sub_lists:
            process_connection = self._one_way_connections[process_id-1].receiving_connection
            process = HashWorker(process_id, self._event_queue, sub_list, self._use_verbose_logging, self._should_check_videos, process_connection, self._enable_redisperse)
            
            self._process_list.insert(process_id-1, process)
            process_id += 1

        self._process_num_processed_list = [0] * len(self._process_list)

    def _replace_process(self, process):
        process_connection = self._one_way_connections[process.process_id-1].receiving_connection
        new_process = HashWorker(process.process_id, self._event_queue, self._sub_lists[process.process_id-1], self._use_verbose_logging, self._should_check_videos, process_connection, self._enable_redisperse)
        return new_process