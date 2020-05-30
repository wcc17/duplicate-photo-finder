import sys
from media_utility import MediaUtility
from event import Event
from event_type import EventType

class HashWorker:

    _media_utility = None
    _process_id = 0
    _queue = None

    def __init__(self, process_id, queue):
        self._media_utility = MediaUtility()
        self._process_id = process_id
        self._queue = queue

    def execute(self, file_list):
        for filepath in file_list:
           self.__handle_filepath(filepath)

        self.__add_to_queue(EventType.PROCESS_DONE, None)

    def __handle_filepath(self, filepath):
        if self._media_utility.is_image_file(filepath):
            self.__handle_valid_image(filepath)
        elif self._media_utility.is_video_file(filepath): #TODO: Only check videos if a flag is set
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
        self._queue.put(Event(event_type, event_data, self._process_id))