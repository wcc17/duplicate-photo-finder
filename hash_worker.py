import sys
from media_utility import MediaUtility
from event import Event
from event_type import EventType
from multiprocessing import Process
from logger import Logger

class HashWorker(Process):

    _media_utility = None
    _process_id = 0
    _event_queue = None
    _task_queue = None
    _file_list = []
    _should_check_videos = False
    _logger = None

    def __init__(self, process_id, use_verbose_logging, should_check_videos, event_queue, task_queue):
        super(HashWorker, self).__init__()

        self._media_utility = MediaUtility(use_verbose_logging)
        self._logger = Logger()
        self._process_id = process_id
        self._should_check_videos = should_check_videos
        self._event_queue = event_queue
        self._task_queue = task_queue
    
    def run(self):
        self.__execute()

    def __execute(self):
        while True:
            filepath = self._task_queue.get()

            if(filepath == -1):
                break
            elif isinstance(filepath, str):
                self._logger.print_log(str(self._process_id) + ": processing filepath " + filepath)
                self.__handle_filepath(filepath)
                self.__add_to_queue(EventType.PROCESS_DONE, None)
            else:
                self._logger.print_log(str(self._process_id) + ": picked up something strange from the queue")

    def __handle_filepath(self, filepath):
        if self._media_utility.is_image_file(filepath):
            self.__handle_valid_image(filepath)
        elif self._should_check_videos and self._media_utility.is_video_file(filepath):
            self.__handle_valid_video(filepath)
        else:
            self.__handle_no_valid_media_found(filepath)

    def __handle_valid_image(self, filepath):
        image_model = self._media_utility.get_media_model_for_image(filepath)
        self.__handle_valid_media(filepath, image_model)

    def __handle_valid_video(self, filepath):
        video_model = self._media_utility.get_media_model_for_video(filepath)
        self.__handle_valid_media(filepath, video_model)

    def __handle_valid_media(self, filepath, media_model):
        if media_model == None:
            self.__handle_no_valid_media_found(filepath)
        else:
            self.__add_to_queue(EventType.FILE_HASHED, media_model)

    def __handle_no_valid_media_found(self, filepath):
        self.__add_to_queue(EventType.SKIPPED_FILE_HASH, filepath)

    def __add_to_queue(self, event_type, event_data):
        self._event_queue.put(Event(event_type, event_data, self._process_id))