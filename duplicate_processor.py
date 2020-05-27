from multiprocessing import Process, Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_file_handler import DuplicateProcessorFileHandler
from logger import Logger
from queue_item_type import QueueItemType
import os
import time
import sys
import numpy

class DuplicateProcessor:

    _output_directory_path = None
    _duplicates_folder_path = None
    _originals_folder_path = None
    _rescan_for_duplicates = False
    _omit_known_duplicates = False
    _process_count = 0
    _file_handler = None
    _logger = None

    _known_non_duplicates = []
    _known_duplicates = []
    _files_that_failed_to_load = []
    _skipped_files = []
    _ommitted_known_files = []

    def __init__(self, output_directory_path, duplicates_folder_path, originals_folder_path, rescan_for_duplicates, omit_known_duplicates, process_count):
        self._duplicates_folder_path = duplicates_folder_path
        self._originals_folder_path = originals_folder_path
        self._rescan_for_duplicates = rescan_for_duplicates
        self._omit_known_duplicates = omit_known_duplicates
        self._output_directory_path = output_directory_path
        self._process_count = process_count

        self._logger = Logger()
        self._file_handler = DuplicateProcessorFileHandler(self._output_directory_path)

    def execute(self):
        try:
            self._logger.print_log("backup old output files before writing output to file again...")
            self._file_handler.backup_old_output_files()

            duplicate_folder_files_list = self.__get_files_list(self._duplicates_folder_path, "duplicate folder")
            originals_folder_files_list = self.__get_files_list(self._originals_folder_path, "originals folder")
            duplicate_folder_files_list = self.__handle_processed_duplicates(duplicate_folder_files_list)
            originals_folder_files_list = self.__handle_processed_originals(originals_folder_files_list)
            self.__execute_processes(duplicate_folder_files_list, originals_folder_files_list)

            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)

        except KeyboardInterrupt:
            self._logger.print_log('Interrupted, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            raise
        except Exception:
            self._logger.print_log('Exception occurred, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            raise

    def __execute_processes(self, duplicate_folder_files_list, originals_folder_files_list):
        queue = Queue()
        process_list = []

        #TODO: I would prefer to not use numpy like this
        sub_lists = numpy.array_split(numpy.array(duplicate_folder_files_list), self._process_count)
        sub_lists = numpy.array(sub_lists).tolist()

        for sub_list in sub_lists:
            sub_list = numpy.array(sub_list).tolist()

            process = Process(target=self.__execute_worker, args=(sub_list, originals_folder_files_list, queue))
            process.start()
            # process.join()
            process_list.append(process)

        num_processed = 0
        total_to_process = len(duplicate_folder_files_list)
        while(self.__some_process_is_alive(process_list)):
            #check the queue and do stuff with it
            queue_item = queue.get()
            queue_item_string = queue_item.queue_item_string
            queue_item_type = queue_item.queue_item_type

            if(queue_item_type == QueueItemType.DUPLICATE):
                self._logger.print_log("duplicate found")
                self._known_duplicates.append(queue_item_string)
                num_processed += 1
            elif queue_item_type == QueueItemType.NON_DUPLICATE:
                self._logger.print_log("Unique image found")
                self._known_non_duplicates.append(queue_item_string)
                num_processed += 1
            elif queue_item_type == QueueItemType.SKIPPED:
                self._logger.print_log("skipped a file")
                self._skipped_files.append(queue_item_string)
                num_processed += 1
            elif queue_item_type == QueueItemType.OMITTED_KNOWN:
                self._logger.print_log("omitted known")
                #TODO: this would need to be propagated to all the processes to let them know that they have one less item to check photos against
                self._ommitted_known_files.append(queue_item_string)
                num_processed += 1
            elif queue_item_type == QueueItemType.FAILED_TO_LOAD:
                self._logger.print_log("failed to load")
                self._files_that_failed_to_load.append(queue_item_string)
                num_processed += 1
            
            
            sys.stdout.write("Progress: " + str(num_processed) + "/" + str(total_to_process) + "\r")
            sys.stdout.flush()

        
        #TODO: need to kill the processes if something goes wrong


    def __execute_worker(self, duplicate_folder_files_list, originals_folder_files_list, queue):
        duplicate_processor_worker = DuplicateProcessorWorker()
        duplicate_processor_worker.execute(self._rescan_for_duplicates, self._omit_known_duplicates, duplicate_folder_files_list, originals_folder_files_list, queue)

    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        
        return False

    def __get_files_list(self, path, folder_name): 
        self._logger.print_log("getting " + folder_name + " files list..") 
        file_list = self._file_handler.get_files_list(path, folder_name)  
        
        #make sure all the files are open-able in the list (because windows can be dumb) and keep track of files that can't be loaded for some reason. change path if necessary
        file_list = self.__handle_files_with_bad_paths(file_list)
        
        self._logger.print_log(folder_name + " files count: " + str(len(file_list)))
        return file_list

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