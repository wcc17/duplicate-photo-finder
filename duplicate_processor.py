# -*- coding: utf-8 -*-
import os
import time
import sys
from duplicate_processor_file_handler import DuplicateProcessorFileHandler
from logger import Logger
from image_utility import ImageUtility

class DuplicateProcessor:
    _duplicates_folder_path = None
    _originals_folder_path = None
    _rescan_for_duplicates = False
    _omit_known_duplicates = False

    _known_non_duplicates = []
    _known_duplicates = []
    _files_that_failed_to_load = []
    _skipped_files = []
    _ommitted_known_files = []

    _file_handler = None
    _logger = None
    _image_utility = None

    def execute(self, output_directory_path, duplicates_folder_path, originals_folder_path, rescan_for_duplicates, omit_known_duplicates):
        try:
            self._logger = Logger()
            self._file_handler = DuplicateProcessorFileHandler()
            self._file_handler.initialize(output_directory_path)
            self._image_utility = ImageUtility()
            
            self._duplicates_folder_path = duplicates_folder_path
            self._originals_folder_path = originals_folder_path
            self._rescan_for_duplicates = rescan_for_duplicates
            self._omit_known_duplicates = omit_known_duplicates

            self.__process()
        except KeyboardInterrupt:
            self._logger.print_log('Interrupted, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            raise
        except Exception as e:
            self._logger.print_log('Exception occurred, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            raise

    def __process(self):
        duplicate_folder_files_list = self.__get_files_list(self._duplicates_folder_path, "duplicate folder")
        originals_folder_files_list = self.__get_files_list(self._originals_folder_path, "originals folder")

        duplicate_folder_files_list = self.__handle_processed_duplicates(duplicate_folder_files_list)
        originals_folder_files_list = self.__handle_processed_originals(originals_folder_files_list)
        
        self._logger.print_log("backup old output files before writing output to file again...")
        self._file_handler.backup_old_output_files()

        self.__process_files(duplicate_folder_files_list, originals_folder_files_list)
        
        self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)

    def __process_files(self, duplicate_folder_files_list, originals_folder_files_list):
        self._logger.print_log("begin processing files...")

        num_processed = len(self._known_non_duplicates) + len(self._known_duplicates) + len(self._files_that_failed_to_load) + len(self._skipped_files)
        duplicate_folder_files_length = len(duplicate_folder_files_list)
        duplicate_folder_file_index = 0

        while (duplicate_folder_file_index < len(duplicate_folder_files_list)):
            self._logger.print_log("Processed: " + str(num_processed) + "/" + str(duplicate_folder_files_length) + ", duplicates: " + str(len(self._known_duplicates)) + ", non-duplicates: " + str(len(self._known_non_duplicates)) + ", failed (not compared at all): " + str(len(self._files_that_failed_to_load)) + ", skipped (not compared at all): " + str(len(self._skipped_files)))
            
            duplicate_folder_file = duplicate_folder_files_list[duplicate_folder_file_index]
            duplicate_folder_file_image = self._image_utility.get_valid_image(duplicate_folder_file)

            if(duplicate_folder_file_image == None):
                self._skipped_files.append(duplicate_folder_file)
                duplicate_folder_file_index += 1
                num_processed += 1
                continue

            self._logger.print_log("Processing: " + duplicate_folder_file)
            
            is_duplicate_of_original_folder_image = False
            original_folder_files_processed = 0
            for original_folder_file in originals_folder_files_list:
                is_duplicate_of_original_folder_image = self._image_utility.compare_image_to_file(duplicate_folder_file_image, original_folder_file)

                if(is_duplicate_of_original_folder_image == True):
                    self._logger.print_log("Duplicate found after processing " + str(original_folder_files_processed) + " images from originals folder")
                    
                    if self._rescan_for_duplicates == True:
                        other_duplicates = self.__get_duplicates_after_rescan_for_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
                        duplicate_folder_files_list = [i for i in duplicate_folder_files_list if i not in other_duplicates]
                        num_processed += len(other_duplicates) 

                    if self._omit_known_duplicates == True:
                        self.__handle_omit_known_duplicates(originals_folder_files_list, original_folder_file)

                    break

                original_folder_files_processed += 1
                sys.stdout.write("Progress: " + str(original_folder_files_processed) + "/" + str(len(originals_folder_files_list)) + "\r")
                sys.stdout.flush()

            if(is_duplicate_of_original_folder_image == False):
                self._logger.print_log("No duplicate found")
                self._known_non_duplicates.append(duplicate_folder_file)
            else:
                self._known_duplicates.append(duplicate_folder_file)

            num_processed += 1
            duplicate_folder_file_index += 1
        
        self._logger.print_log("count of files that do not exist in original files folder: " + str(len(self._known_non_duplicates)))

    def __get_duplicates_after_rescan_for_duplicates(self, duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file):
        other_duplicates = []

        self._logger.print_log("Handling any additional duplicates")

        #get any other duplicates that may exist in duplicate_folder_files_list when compared to original_folder_file
        other_duplicates = self.__get_other_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
        
        for dup in other_duplicates:
            #add other duplicates to skipped files so that we write down not to check them again
            self._skipped_files.append(dup)
        
        return other_duplicates

    def __handle_omit_known_duplicates(self, originals_folder_files_list, original_folder_file):
        self._logger.print_log("Removing original_folder_file so we don't check again.")

        #add the file to ommitted_known_files in case we have to reload
        self._ommitted_known_files.append(original_folder_file)

        #stop looking at the original_folder_file
        originals_folder_files_list.remove(original_folder_file)

        self._logger.print_log("New original_folder_files size: " + str(len(originals_folder_files_list)))
        
        return originals_folder_files_list

    def __get_other_duplicates(self, duplicate_folder_files_list, duplicate_image, duplicate_image_path):
        #if we have found a duplicate, we may have the same file multiple times in duplicate_folder_files_list
            #find all instances of "file" in duplicate_folder_files_list
            #delete each one
        #after duplicate_folder_files_list no longer contains the duplicate files, theres no chance that the copy of that file in originals_folder_files_list will need to be checked again. so we can get rid of it
        duplicates = []
        num_processed = 0

        for file_path in duplicate_folder_files_list:
            if(self.__compare_image_to_file(duplicate_image, file_path) == True):
                duplicates.append(file_path)
                
            num_processed += 1
            sys.stdout.write("Progress: " + str(num_processed) + "/" + str(len(duplicate_folder_files_list)) + "\r")
            sys.stdout.flush()

        return duplicates

    def __handle_processed_duplicates(self, duplicate_folder_files_list):
        self._logger.print_log("sort out duplicates files that have already been marked as processed...")

        duplicate_folder_files_list = self.__remove_already_processed_file_paths_from_file(duplicate_folder_files_list, self._file_handler.get_known_non_duplicate_file_path(), self._known_non_duplicates)
        duplicate_folder_files_list = self.__remove_already_processed_file_paths_from_file(duplicate_folder_files_list, self._file_handler.get_known_duplicate_file_path(), self._known_duplicates)
        duplicate_folder_files_list = self.__remove_already_processed_file_paths_from_file(duplicate_folder_files_list, self._file_handler.get_files_that_failed_to_load_file_path(), self._files_that_failed_to_load)
        duplicate_folder_files_list = self.__remove_already_processed_file_paths_from_file(duplicate_folder_files_list, self._file_handler.get_files_skipped_file_path(), self._skipped_files)

        self._logger.print_log("duplicate folder files count after scanning for already processed: " + str(len(duplicate_folder_files_list)))

        return duplicate_folder_files_list

    def __handle_processed_originals(self, originals_folder_files_list):
        if self._rescan_for_duplicates == True:
            self._logger.print_log("handle originals files that have already been marked as processed...")
            originals_folder_files_list = self.__remove_already_processed_file_paths_from_file(originals_folder_files_list, self._file_handler.get_ommitted_known_files_file_path(), self._ommitted_known_files)
            self._logger.print_log("originals folder files count after scanning for already processed: " + str(len(originals_folder_files_list)))

        return originals_folder_files_list 

    def __get_files_list(self, path, folder_name): 
        self._logger.print_log("getting " + folder_name + " files list..") 
        file_list = self._file_handler.get_files_list(path, folder_name)  
        
        #make sure all the files are open-able in the list (because windows can be dumb) and keep track of files that can't be loaded for some reason. change path if necessary
        file_list = self.__handle_files_with_bad_paths(file_list)
        
        self._logger.print_log(folder_name + " files count: " + str(len(file_list)))
        return file_list

    def __handle_files_with_bad_paths(self, file_list):
        for idx in range(len(file_list)):
            try:
                test_time = time.ctime(os.path.getctime(file_list[idx]))
            except:
                try:
                    if(os.name == 'nt'):
                        #windows doesn't allow very long filepaths. we can check here to fix that and still open the file. NOTE: this works, but it doesn't seem like os.walk(path) is getting all files when running from Windows
                        #windows applies this to the beginning of the path: \\?\
                        new_path = "\\\\?\\"
                        new_path = new_path + file_list[idx]
                        test_time = time.ctime(os.path.getctime(new_path))

                        file_list[idx] = new_path
                    else:
                        self._files_that_failed_to_load.append(file_list[idx])
                except:
                    self._files_that_failed_to_load.append(file_list[idx])

        #remove the failed files, no reason to bother trying to compare them. we didn't change anything about these if we failed to open up the created time and it failed
        if(len(self._files_that_failed_to_load) > 0):
            self._logger.print_log("Removing " + str(len(self._files_that_failed_to_load)) + " files from files_list. They will not be processed because they can't be opened")
            self._logger.print_log("file_list size: " + str(len(file_list)))
            
            file_list = [i for i in file_list if i not in self._files_that_failed_to_load]
            self._logger.print_log("file_list size: " + str(len(file_list)))
        
        return file_list

    def __remove_already_processed_file_paths_from_file(self, file_list, file_name, file_list_to_add_to):
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
            return file_list
        except:
            self._logger.print_log("Couldn't open " + file_name + ", maybe it doesn't exist. Moving on")
            return file_list
