# -*- coding: utf-8 -*-
import os
from logger import Logger

class DuplicateProcessorFileHandler:
    KNOWN_NON_DUPLICATES_FILE_NAME = "non-duplicates.txt"
    KNOWN_DUPLICATES_FILE_NAME = "duplicates.txt"
    FILES_THAT_FAILED_TO_LOAD_FILE_NAME = "files_that_failed_to_load.txt"
    SKIPPED_FILES_FILE_NAME = "skipped_files.txt"
    OMMITTED_KNOWN_FILES_FILE_NAME = "ommitted_known_files.txt"

    _known_non_duplicates_file_path = None
    _known_duplicates_file_path = None
    _files_that_failed_to_load_file_path = None
    _skipped_files_file_path = None
    _ommitted_known_files_file_path = None

    _logger = None

    def initialize(self, output_directory_path):
        self._logger = Logger()

        self.__initialize_file_paths(output_directory_path)
    
    def get_files_list(self, path, folder_name): 
        file_list = []   

        #add all files to file_list                                                                                              
        for root, directories, files in os.walk(path):
            for file in files:
                file_list.append(os.path.join(root, file))
        
        return file_list

    def write_output_for_files(self, known_non_duplicates, known_duplicates, files_that_failed_to_load, skipped_files, ommitted_known_files):
        self.__write_output_for_file(self._known_non_duplicates_file_path, known_non_duplicates)
        self.__write_output_for_file(self._known_duplicates_file_path, known_duplicates)
        self.__write_output_for_file(self._files_that_failed_to_load_file_path, files_that_failed_to_load)
        self.__write_output_for_file(self._skipped_files_file_path, skipped_files)
        self.__write_output_for_file(self._ommitted_known_files_file_path, ommitted_known_files)

    def backup_old_output_files(self):
        known_non_duplicates_backup_path = self._known_non_duplicates_file_path + ".BACKUP"
        known_duplicates_backup_path = self._known_duplicates_file_path + ".BACKUP"
        files_that_failed_to_load_backup_path = self._files_that_failed_to_load_file_path + ".BACKUP"
        skipped_files_backup_path = self._skipped_files_file_path + ".BACKUP"
        ommitted_known_files_backup_path = self._ommitted_known_files_file_path + ".BACKUP"

        self.__remove_file(known_non_duplicates_backup_path)
        self.__remove_file(known_duplicates_backup_path)
        self.__remove_file(files_that_failed_to_load_backup_path)
        self.__remove_file(skipped_files_backup_path)
        self.__remove_file(ommitted_known_files_backup_path)

        self.__rename_file(self._known_non_duplicates_file_path, known_non_duplicates_backup_path)
        self.__rename_file(self._known_duplicates_file_path, known_duplicates_backup_path)
        self.__rename_file(self._files_that_failed_to_load_file_path, files_that_failed_to_load_backup_path)
        self.__rename_file(self._skipped_files_file_path, skipped_files_backup_path)
        self.__rename_file(self._ommitted_known_files_file_path, ommitted_known_files_backup_path)

    def get_known_non_duplicate_file_path(self):
        return self._known_non_duplicates_file_path
    
    def get_known_duplicate_file_path(self):
        return self._known_duplicates_file_path

    def get_files_that_failed_to_load_file_path(self):
        return self._files_that_failed_to_load_file_path

    def get_files_skipped_file_path(self):
        return self._skipped_files_file_path

    def get_ommitted_known_files_file_path(self):
        return self._ommitted_known_files_file_path
    
    def __initialize_file_paths(self, output_directory_path):
        self._known_non_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_NON_DUPLICATES_FILE_NAME)
        self._known_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_DUPLICATES_FILE_NAME)
        self._files_that_failed_to_load_file_path = os.path.join(output_directory_path, self.FILES_THAT_FAILED_TO_LOAD_FILE_NAME)
        self._skipped_files_file_path = os.path.join(output_directory_path, self.SKIPPED_FILES_FILE_NAME)
        self._ommitted_known_files_file_path = os.path.join(output_directory_path, self.OMMITTED_KNOWN_FILES_FILE_NAME)

    def __remove_file(self, filename):
        try:
            os.remove(filename)
        except:
            self._logger.print_log("Could not remove " + filename + ", probably doesn't exist. Moving on")

    def __rename_file(self, old_file_name, new_file_name):
        try:
            os.rename(old_file_name, new_file_name)
        except:
            self._logger.print_log("Could not rename " + old_file_name + ", probably doesn't exist. Moving on")

    def __write_output_for_file(self, file_name, list_of_files):
        output_file = open(file_name, 'w+')
        for file in list_of_files:
            output_to_write = str(file) + "\n"
            output_file.write(output_to_write)

    def __initialize_file_paths(self, output_directory_path):
        self._known_non_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_NON_DUPLICATES_FILE_NAME)
        self._known_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_DUPLICATES_FILE_NAME)
        self._files_that_failed_to_load_file_path = os.path.join(output_directory_path, self.FILES_THAT_FAILED_TO_LOAD_FILE_NAME)
        self._skipped_files_file_path = os.path.join(output_directory_path, self.SKIPPED_FILES_FILE_NAME)
        self._ommitted_known_files_file_path = os.path.join(output_directory_path, self.OMMITTED_KNOWN_FILES_FILE_NAME)