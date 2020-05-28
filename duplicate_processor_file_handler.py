# -*- coding: utf-8 -*-
import os
import hashlib
import sys
from logger import Logger
from duplicate_processor_output_file_handler import DuplicateProcessorOutputFileHandler
from image_utility import ImageUtility
from image_model import ImageModel

class DuplicateProcessorFileHandler:
    _logger = None
    _output_file_handler = None
    _image_utility = None

    _known_non_duplicates = []
    _known_duplicates = []
    _skipped_files = []

    def __init__(self, output_directory_path):
        self._logger = Logger()
        self._output_file_handler = DuplicateProcessorOutputFileHandler(output_directory_path)
        self._image_utility = ImageUtility()
    
    def get_possible_duplicates_image_models(self, path, folder_name): 
        file_list = self.__get_files_list(path, folder_name)
        self.__handle_processed_duplicates(file_list)
        
        image_models = self.__get_image_models(file_list, True)
        self._logger.print_log(folder_name + " image model count: " + str(len(file_list)))

        return image_models

    def get_originals_image_models(self, path, folder_name):
        file_list = self.__get_files_list(path, folder_name)
        image_models = self.__get_image_models(file_list, False)
        self._logger.print_log(folder_name + " image model from count: " + str(len(file_list)))

        return image_models

    def get_already_processed_file_info(self):
        return (self._known_non_duplicates, self._known_duplicates, self._skipped_files)

    def backup_old_output_files(self):
        self._output_file_handler.backup_old_output_files()

    def write_output_for_files(self, known_non_duplicates, known_duplicates, skipped_files):
        self._output_file_handler.write_output_for_files(known_non_duplicates, known_duplicates, skipped_files)

    def __get_files_list(self, path, folder_name):
        self._logger.print_log("getting " + folder_name + " files list..")
        file_list = []   

        #add all files to file_list                                                                                              
        for root, directories, files in os.walk(path):
            for file in files:
                file_list.append(os.path.join(root, file))

        return file_list

    def __handle_processed_duplicates(self, potential_duplicate_folder_files_list):
        self._logger.print_log("sort out duplicates files that have already been marked as processed...")

        self._output_file_handler.remove_already_processed_file_paths_from_list(potential_duplicate_folder_files_list, self._output_file_handler.get_known_non_duplicates_file_path(), self._known_non_duplicates)
        self._output_file_handler.remove_already_processed_file_paths_from_list(potential_duplicate_folder_files_list, self._output_file_handler.get_known_duplicates_file_path(), self._known_duplicates)
        self._output_file_handler.remove_already_processed_file_paths_from_list(potential_duplicate_folder_files_list, self._output_file_handler.get_skipped_files_file_path(), self._skipped_files)

        self._logger.print_log("duplicate folder files count after scanning for already processed: " + str(len(potential_duplicate_folder_files_list)))

    def __get_image_models(self, file_list, use_skipped_files):
        image_models = []
        image = None
        num_processed = 0
        files_removed = 0

        for filepath in file_list:
            image = self._image_utility.get_valid_image(filepath)

            if(image == None):
                if use_skipped_files:
                    self._skipped_files.append(filepath)
                files_removed += 1
            else:
                hash = hashlib.md5(image.tobytes())
                image_model = ImageModel(filepath, hash.hexdigest())
                image_models.append(image_model)

            num_processed += 1

            sys.stdout.write("Processed: " + str(num_processed) + "/" + str(len(file_list)) + " hashes " + "\r")
            sys.stdout.flush()

        if(files_removed > 0):
            self._logger.print_log("Removed " + str(files_removed) + " files and added to skipped. They will not be processed because they can't be opened or they are not images")
        
        return image_models