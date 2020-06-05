# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from event import Event
from event_type import EventType
from duplicate_result_model import DuplicateResultModel
from multiprocessing import Process
from media_model import MediaModel

class DuplicateProcessorWorker(Process):
    _task_queue = None
    _event_queue = None
    _process_id = 0
    _originals_image_models = []
    _logger = []
    _use_verbose_logging = False

    def __init__(self, process_id, task_queue, event_queue, originals_image_models, use_verbose_logging):
        super(DuplicateProcessorWorker, self).__init__()

        self._process_id = process_id
        self._originals_image_models = originals_image_models
        self._task_queue = task_queue
        self._event_queue = event_queue
        self._use_verbose_logging = use_verbose_logging
        self._logger = Logger()

    def run(self):
        self.__execute()

    def __execute(self):
        while True:
            potential_duplicate_media_model = self._task_queue.get()

            if(potential_duplicate_media_model == -1):
                break
            elif isinstance(potential_duplicate_media_model, MediaModel):
                self.__log_verbose(str(self._process_id) + ": processing file " + potential_duplicate_media_model.filepath)
                
                matching_originals_model = self.__compare_model_to_originals(potential_duplicate_media_model)
                self.__handle_comparison_result(potential_duplicate_media_model, matching_originals_model)
            else:
                self._logger.print_log(str(self._process_id) + " picked up something strange from the queue" + str(potential_duplicate_media_model))

    def __compare_model_to_originals(self, image_model):
        matching_originals_model = None
        for original_image_model in self._originals_image_models:
            
            if self.__compare_models(image_model, original_image_model) == True:
                matching_originals_model = original_image_model
                break

        return matching_originals_model

    def __compare_models(self, image_model1, image_model2):
        if image_model1.hash == image_model2.hash:
            if not image_model1.filepath == image_model2.filepath:
                return True

        return False

    def __handle_comparison_result(self, potential_duplicate_image_model, matching_originals_model):
        if(matching_originals_model is None):
            self.__add_to_queue(EventType.NON_DUPLICATE, potential_duplicate_image_model)
        else:
            self.__add_to_queue(EventType.DUPLICATE, DuplicateResultModel(potential_duplicate_image_model.filepath, matching_originals_model.filepath))

    def __add_to_queue(self, event_type, event_data):
        self._event_queue.put(Event(event_type, event_data, self._process_id))

    def __log_verbose(self, message):
        if self._use_verbose_logging == True:
            self._logger.print_log(message)