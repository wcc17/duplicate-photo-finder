import hashlib
import sys
from image_utility import ImageUtility
from image_model import ImageModel
from event import Event
from event_type import EventType

class HashWorker:

    _image_utility = None
    _process_id = 0
    _queue = None

    def __init__(self, process_id, queue):
        self._image_utility = ImageUtility()
        self._process_id = process_id
        self._queue = queue

    def execute(self, file_list, append_to_skipped):
        image = None

        for filepath in file_list:
            image = self._image_utility.get_valid_image(filepath)

            if(image == None):
                if append_to_skipped:
                    self.__add_to_queue(EventType.SKIPPED_FILE_HASH, filepath)
            else:
                try:
                    hash = hashlib.md5(image.tobytes())
                    image_model = ImageModel(filepath, hash.hexdigest())
                    self.__add_to_queue(EventType.FILE_HASHED, image_model)
                except:
                    self.__add_to_queue(EventType.SKIPPED_FILE_HASH, filepath)

        self.__add_to_queue(EventType.PROCESS_DONE, None)

    def __add_to_queue(self, event_type, event_data):
        self._queue.put(Event(event_type, event_data, self._process_id))