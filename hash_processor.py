from processor_file_handler import ProcessorFileHandler
from base_processor import BaseProcessor
from hash_event_handler import HashEventHandler
from event_type import EventType
from media_utility import MediaUtility
from hash_worker import HashWorker

class HashProcessor(BaseProcessor):

    _hash_event_handler = None
    _use_verbose_logging = False
    _should_check_videos = False
    _media_utility = None

    def __init__(self, file_handler, use_verbose_logging, should_check_videos, process_count):
        super().__init__(file_handler, process_count)
        self._hash_event_handler = HashEventHandler(use_verbose_logging)
        self._use_verbose_logging = use_verbose_logging
        self._should_check_videos = should_check_videos
        self._media_utility = MediaUtility(self._use_verbose_logging)

    def process(self, folder_path, folder_name, skipped_files, append_to_skipped):
        self._process_list = []
        image_models = []

        filepaths = self._file_handler.get_filepaths(folder_path, folder_name)
        num_filepaths = len(filepaths)

        self._logger.print_log("Number of files found in " + folder_name + " to attempt to md5 hash: " + str(num_filepaths) + ". Starting hash process. ")
        
        self._run_processes(filepaths, self._hash_event_handler.handle_event, (image_models, skipped_files, append_to_skipped))

        self._logger.print_log("Hashed " + str(len(image_models)) + " media files" + " and skipped " + str(num_filepaths - len(image_models)) + ". ")
        return image_models

    def _get_process(self, process_id):
        return HashWorker(process_id, self._use_verbose_logging, self._should_check_videos, self._event_queue, self._task_queue)