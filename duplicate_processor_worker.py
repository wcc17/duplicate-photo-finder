# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from image_utility import ImageUtility
from event import Event
from event_type import EventType

class DuplicateProcessorWorker:
    _rescan_for_duplicates = False
    _omit_known_duplicates = False
    _image_utility = None
    _queue = None
    _total_to_process = 0
    _process_id = 0

    def __init__(self, rescan_for_duplicates, omit_known_duplicates, process_id, queue):
        self._image_utility = ImageUtility()
        self._rescan_for_duplicates = rescan_for_duplicates
        self._omit_known_duplicates = omit_known_duplicates
        self._process_id = process_id
        self._queue = queue

    def execute(self, duplicate_folder_files_list, originals_folder_files_list):
        # self._logger.print_log("begin processing files...")

        # TODO: logger statements should be in duplicate_processor, not the worker
        # num_processed = len(self._known_non_duplicates) + len(self._known_duplicates) + len(self._files_that_failed_to_load) + len(self._skipped_files)
        duplicate_folder_files_length = len(duplicate_folder_files_list)
        duplicate_folder_file_index = 0

        while (duplicate_folder_file_index < len(duplicate_folder_files_list)):
            # TODO: logger statements should be in duplicate_processor, not the worker
            # self._logger.print_log("Processed: " + str(num_processed) + "/" + str(duplicate_folder_files_length) + ", duplicates: " + str(len(self._known_duplicates)) + ", non-duplicates: " + str(len(self._known_non_duplicates)) + ", failed (not compared at all): " + str(len(self._files_that_failed_to_load)) + ", skipped (not compared at all): " + str(len(self._skipped_files)))
            
            duplicate_folder_file = duplicate_folder_files_list[duplicate_folder_file_index]
            duplicate_folder_file_image = self._image_utility.get_valid_image(duplicate_folder_file)

            if(duplicate_folder_file_image == None):
                self.__add_to_queue(EventType.SKIPPED, duplicate_folder_file)
                duplicate_folder_file_index += 1
                continue

            # self._logger.print_log("Processing: " + duplicate_folder_file)
            
            is_duplicate_of_original_folder_image = False
            original_folder_files_processed = 0
            for original_folder_file in originals_folder_files_list:
                is_duplicate_of_original_folder_image = self._image_utility.compare_image_to_file(duplicate_folder_file_image, original_folder_file)

                if(is_duplicate_of_original_folder_image == True):
                    # self._logger.print_log("Duplicate found after processing " + str(original_folder_files_processed) + " images from originals folder")
                    self.__get_duplicates_after_rescan_for_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
                    originals_folder_files_list = self.__handle_omit_known_duplicates(originals_folder_files_list, original_folder_file)
                    break

                original_folder_files_processed += 1
                # sys.stdout.write("Progress: " + str(original_folder_files_processed) + "/" + str(len(originals_folder_files_list)) + "\r")
                # sys.stdout.flush()

            if(is_duplicate_of_original_folder_image == False):
                self.__add_to_queue(EventType.NON_DUPLICATE, duplicate_folder_file)
            else:
                self.__add_to_queue(EventType.DUPLICATE, duplicate_folder_file)

            # TODO: should be handled in duplicate_processor
            # num_processed += 1
            duplicate_folder_file_index += 1

    def __get_duplicates_after_rescan_for_duplicates(self, duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file):
        if self._rescan_for_duplicates == True:
            other_duplicates = []

            #get any other duplicates that may exist in duplicate_folder_files_list when compared to original_folder_file
            other_duplicates = self.__get_other_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
            
            for dup in other_duplicates:
                #add other duplicates to skipped files so that we write down not to check them again
                self.__add_to_queue(EventType.SKIPPED, dup)

            duplicate_folder_files_list = [i for i in duplicate_folder_files_list if i not in other_duplicates]

            # TODO: should be handled in duplicate_processor. also this was the wrong place to do this?????
            # num_processed += len(other_duplicates) 

    def __handle_omit_known_duplicates(self, originals_folder_files_list, original_folder_file):
        if self._omit_known_duplicates == True:
            # self._logger.print_log("Removing original_folder_file so we don't check again.")

            #add the file to ommitted_known_files in case we have to reload
            self.__add_to_queue(EventType.OMITTED_KNOWN, original_folder_file)

            #stop looking at the original_folder_file
            originals_folder_files_list.remove(original_folder_file)

            # self._logger.print_log("New original_folder_files size: " + str(len(originals_folder_files_list)))
            
        return originals_folder_files_list

    def __get_other_duplicates(self, duplicate_folder_files_list, duplicate_image, duplicate_image_path):
        #if we have found a duplicate, we may have the same file multiple times in duplicate_folder_files_list
            #find all instances of "file" in duplicate_folder_files_list
            #delete each one
        #after duplicate_folder_files_list no longer contains the duplicate files, theres no chance that the copy of that file in originals_folder_files_list will need to be checked again. so we can get rid of it
        duplicates = []
        num_processed = 0

        for file_path in duplicate_folder_files_list:
            if(self._image_utility.compare_image_to_file(duplicate_image, file_path) == True):
                duplicates.append(file_path)
                
            num_processed += 1
            # sys.stdout.write("Progress: " + str(num_processed) + "/" + str(len(duplicate_folder_files_list)) + "\r")
            # sys.stdout.flush()

        return duplicates

    def __add_to_queue(self, event_type, event_string):
        self._queue.put(Event(event_type, event_string, self._process_id))
