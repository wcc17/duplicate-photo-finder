# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from duplicate_processor_output_file_handler import DuplicateProcessorOutputFileHandler
from image_model import ImageModel

class DuplicateProcessorFileHandler:
    _logger = None
    _output_file_handler = None

    _known_non_duplicates = []
    _known_duplicates = []
    _skipped_files = []

    def __init__(self, output_directory_path):
        self._logger = Logger()
        self._output_file_handler = DuplicateProcessorOutputFileHandler(output_directory_path)

    def get_possible_duplicates_filepaths(self, path, folder_name): 
        file_list = self.__get_files_list(path, folder_name)
        self.__handle_processed_duplicates(file_list)
        return file_list

    def get_originals_filepaths(self, path, folder_name):
        file_list = self.__get_files_list(path, folder_name)
        return file_list

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