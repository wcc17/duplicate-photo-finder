# -*- coding: utf-8 -*-
import os
import sys
from logger import Logger
from processor_output_file_handler import ProcessorOutputFileHandler

class ProcessorFileHandler:
    _logger = None
    _output_file_handler = None

    def __init__(self, output_file_path):
        self._logger = Logger()
        self._output_file_handler = ProcessorOutputFileHandler(output_file_path)

    def get_filepaths(self, path, folder_name):
        file_list = self.__get_files_list(path, folder_name)
        return file_list

    def write_output_for_files(self, known_non_duplicates, known_duplicates, skipped_files):
        self._logger.print_log("backup old output files before writing output to file...")
        self.__backup_old_output_files()
        self._output_file_handler.write_output_for_files(known_non_duplicates, known_duplicates, skipped_files)
        self._logger.print_log("information written to output files")

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