# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from image_utility import ImageUtility
from event import Event
from event_type import EventType
from duplicate_result_model import DuplicateResultModel

class DuplicateProcessorWorker:
    _rescan_for_duplicates = False
    _omit_known_duplicates = False
    _image_utility = None
    _queue = None
    _total_to_process = 0
    _process_id = 0

    def __init__(self, process_id, queue):
        self._image_utility = ImageUtility()
        self._process_id = process_id
        self._queue = queue

    def execute(self, potential_duplicate_image_models, originals_image_models):

        for potential_duplicate_image_model in potential_duplicate_image_models:
            
            duplicate_found = False
            for original_image_model in originals_image_models:

                if potential_duplicate_image_model.hash == original_image_model.hash:
                    if not potential_duplicate_image_model.filepath == original_image_model.filepath:
                        duplicate_found = True
                
                if(duplicate_found == True):
                    break

            if(duplicate_found == False):
                self.__add_to_queue(EventType.NON_DUPLICATE, potential_duplicate_image_model)
            else:
                self.__add_to_queue(EventType.DUPLICATE, DuplicateResultModel(potential_duplicate_image_model.filepath, original_image_model.filepath))
        
        self.__add_to_queue(EventType.PROCESS_DONE, None)

    def __add_to_queue(self, event_type, event_data):
        self._queue.put(Event(event_type, event_data, self._process_id))
