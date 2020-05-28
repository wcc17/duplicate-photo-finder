import os
from logger import Logger

class DuplicateProcessorOutputFileHandler:

    _logger = None

    KNOWN_NON_DUPLICATES_FILE_NAME = "non-duplicates.txt"
    KNOWN_DUPLICATES_FILE_NAME = "duplicates.txt"
    SKIPPED_FILES_FILE_NAME = "skipped_files.txt"

    _known_non_duplicates_file_path = None
    _known_duplicates_file_path = None
    _skipped_files_file_path = None

    def __init__(self, output_directory_path):
        self._logger = Logger()
        self.__initialize_file_paths(output_directory_path)
    
    def write_output_for_files(self, known_non_duplicates, known_duplicates, skipped_files):
        self.__write_output_for_file(self._known_non_duplicates_file_path, known_non_duplicates)
        self.__write_output_for_file(self._known_duplicates_file_path, known_duplicates)
        self.__write_output_for_file(self._skipped_files_file_path, skipped_files)

    def backup_old_output_files(self):
        known_non_duplicates_backup_path = self._known_non_duplicates_file_path + ".BACKUP"
        known_duplicates_backup_path = self._known_duplicates_file_path + ".BACKUP"
        skipped_files_backup_path = self._skipped_files_file_path + ".BACKUP"

        self.__remove_file(known_non_duplicates_backup_path)
        self.__remove_file(known_duplicates_backup_path)
        self.__remove_file(skipped_files_backup_path)

        self.__rename_file(self._known_non_duplicates_file_path, known_non_duplicates_backup_path)
        self.__rename_file(self._known_duplicates_file_path, known_duplicates_backup_path)
        self.__rename_file(self._skipped_files_file_path, skipped_files_backup_path)

    def remove_already_processed_file_paths_from_list(self, file_list, file_name, file_list_to_add_to):
        try:
            file_to_read = open(file_name, 'r')
            with file_to_read as fp:
                line = fp.readline()
                count = 1
                while line:
                    filename = line.strip()

                    if filename in file_list: file_list.remove(filename)
                    file_list_to_add_to.append(filename)

                    line = fp.readline()
                    count += 1
            
            file_to_read.close()
        except:
            self._logger.print_log("Couldn't open " + file_name + ", maybe it doesn't exist. Moving on")

    def get_known_non_duplicates_file_path(self):
        return self._known_non_duplicates_file_path
    
    def get_known_duplicates_file_path(self):
        return self._known_duplicates_file_path

    def get_skipped_files_file_path(self):
        return self._skipped_files_file_path

    def __initialize_file_paths(self, output_directory_path):
        self._known_non_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_NON_DUPLICATES_FILE_NAME)
        self._known_duplicates_file_path = os.path.join(output_directory_path, self.KNOWN_DUPLICATES_FILE_NAME)
        self._skipped_files_file_path = os.path.join(output_directory_path, self.SKIPPED_FILES_FILE_NAME)
    
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
