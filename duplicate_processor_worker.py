# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from event import Event
from event_type import EventType
from duplicate_result_model import DuplicateResultModel
from base_worker import BaseWorker

class DuplicateProcessorWorker(BaseWorker):

    _rescan_for_duplicates = False
    _omit_known_duplicates = False
    _total_to_process = 0
    _originals_image_models = []

    def __init__(self, process_id, queue, potential_duplicate_image_models, originals_image_models, connection, use_verbose_logging):
        super().__init__(process_id, potential_duplicate_image_models, queue, connection, use_verbose_logging)
        self._originals_image_models = originals_image_models

    def run(self):
        self.__execute()

    def __execute(self):
        files_to_remove = []
        for potential_duplicate_image_model in self.file_list:
            matching_originals_model = self.__compare_model_to_originals(potential_duplicate_image_model)
            self.__handle_comparison_result(potential_duplicate_image_model, matching_originals_model)
            
            files_to_remove.append(potential_duplicate_image_model)
            if self._redisperse_message_received():
                break
        
        self._clear_already_processed_files(files_to_remove)
        self.__add_to_queue(EventType.PROCESS_DONE, None)

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
        self._queue.put(Event(event_type, event_data, self.process_id))