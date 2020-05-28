# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from duplicate_processor_output_file_handler import DuplicateProcessorOutputFileHandler
from image_model import ImageModel

class DuplicateProcessorFileHandler:
    _logger = None
    _output_file_handler = None

    def __init__(self, output_directory_path):
        self._logger = Logger()
        self._output_file_handler = DuplicateProcessorOutputFileHandler(output_directory_path)

    def get_filepaths(self, path, folder_name):
        file_list = self.__get_files_list(path, folder_name)
        return file_list

    def write_output_for_files(self, known_non_duplicates, known_duplicates, skipped_files):
        self._logger.print_log("backup old output files before writing output to file...")
        self.__backup_old_output_files()
        self._output_file_handler.write_output_for_files(known_non_duplicates, known_duplicates, skipped_files)

    def handle_processed_duplicates(self, files_list, known_non_duplicates, known_duplicates, skipped_files):
        self._logger.print_log("sort out duplicates files that have already been marked as processed...")

        self._output_file_handler.remove_already_processed_file_paths_from_list(files_list, self._output_file_handler.get_known_non_duplicates_file_path(), known_non_duplicates)
        self._output_file_handler.remove_already_processed_file_paths_from_list(files_list, self._output_file_handler.get_known_duplicates_file_path(), known_duplicates)
        self._output_file_handler.remove_already_processed_file_paths_from_list(files_list, self._output_file_handler.get_skipped_files_file_path(), skipped_files)

        self._logger.print_log("duplicate folder files count after scanning for already processed: " + str(len(files_list)))

    def __get_files_list(self, path, folder_name):
        self._logger.print_log("getting " + folder_name + " files list..")
        file_list = []   

        #add all files to file_list                                                                                              
        for root, directories, files in os.walk(path):
            for file in files:
                file_list.append(os.path.join(root, file))

        return file_list
    
    def __backup_old_output_files(self):
        self._output_file_handler.backup_old_output_files()