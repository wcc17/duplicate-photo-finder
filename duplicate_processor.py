from multiprocessing import Process, Queue
from duplicate_processor_worker import DuplicateProcessorWorker
from duplicate_processor_file_handler import DuplicateProcessorFileHandler
from logger import Logger
from event_type import EventType
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
        process_list = []
        event_queue = Queue()

        try:
            self._logger.print_log("backup old output files before writing output to file again...")

            duplicate_folder_files_list = self.__get_files_list(self._duplicates_folder_path, "duplicate folder")
            originals_folder_files_list = self.__get_files_list(self._originals_folder_path, "originals folder")
            duplicate_folder_files_list = self.__handle_processed_duplicates(duplicate_folder_files_list)
            originals_folder_files_list = self.__handle_processed_originals(originals_folder_files_list)

            self._file_handler.backup_old_output_files()

            sub_lists = self.__split_list_into_n_lists(duplicate_folder_files_list, self._process_count)
            process_list = self.__setup_and_start_processes(sub_lists, originals_folder_files_list, event_queue)
            total_to_process = len(duplicate_folder_files_list)

            self.__run_processes(event_queue, total_to_process, process_list, sub_lists)
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)

        except KeyboardInterrupt:
            self._logger.print_log('Interrupted, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            self.__kill_processes(process_list)
            raise
        except Exception:
            self._logger.print_log('Exception occurred, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._files_that_failed_to_load, self._skipped_files, self._ommitted_known_files)
            self.__kill_processes(process_list)
            raise

    def __setup_and_start_processes(self, sub_lists, originals_folder_files_list, event_queue):
        process_list  =[]

        process_id = 1
        for sub_list in sub_lists:
            sub_list = numpy.array(sub_list).tolist()

            process = Process(target=self.__execute_worker, args=(sub_list, originals_folder_files_list, event_queue, process_id))
            process.start()
            # process.join()
            process_list.append(process)
            process_id += 1
        
        return process_list

    def __run_processes(self, event_queue, total_to_process, process_list, sub_lists):
        num_processed = 0
        while(self.__some_process_is_alive(process_list)):
            num_processed = self.__handle_event(num_processed, event_queue)

            sys.stdout.write("Overall Progress: " + str(num_processed) + "/" + str(total_to_process) + "\r")
            # for(process in process_list):
            #     sys.stdout.write("Process #" +)
            sys.stdout.flush()

    def __handle_event(self, num_processed, event_queue):
        #check the event_queue and do stuff with it
        event = event_queue.get()
        event_process_id = event.event_process_id
        event_string = event.event_string
        event_type = event.event_type

        if(event_type == EventType.DUPLICATE):
            self.__log_process_message(event_process_id, "Duplicate found: " + event_string)
            self._known_duplicates.append(event_string)
            num_processed += 1
        elif event_type == EventType.NON_DUPLICATE:
            self.__log_process_message(event_process_id, "Unique image found: " + event_string)
            self._known_non_duplicates.append(event_string)
            num_processed += 1
        elif event_type == EventType.SKIPPED:
            self.__log_process_message(event_process_id, "Skipped file: " + event_string)
            self._skipped_files.append(event_string)
            num_processed += 1
        elif event_type == EventType.OMITTED_KNOWN:
            #TODO: this would need to be propagated to all the processes to let them know that they have one less item to check photos against
            self.__log_process_message(event_process_id, "Omitted known duplicate: " + event_string)
            self._ommitted_known_files.append(event_string)
            num_processed += 1
        elif event_type == EventType.FAILED_TO_LOAD:
            self.__log_process_message(event_process_id, "Failed to load file: " + event_string)
            self._files_that_failed_to_load.append(event_string)
            num_processed += 1
        
        return num_processed
        
    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        
        return False

    def __execute_worker(self, duplicate_folder_files_list, originals_folder_files_list, queue, process_id):
        duplicate_processor_worker = DuplicateProcessorWorker(self._rescan_for_duplicates, self._omit_known_duplicates, process_id, queue)
        duplicate_processor_worker.execute(duplicate_folder_files_list, originals_folder_files_list)

    def __split_list_into_n_lists(self, list, number_of_lists):
        #TODO: I would prefer to not use numpy like this
        sub_lists = numpy.array_split(numpy.array(list), number_of_lists)
        sub_lists = numpy.array(sub_lists).tolist()
        return sub_lists

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

    def __kill_processes(self, process_list):
        self._logger.print_log("Terminating all processes")
        for process in process_list:
            process.terminate()
        self._logger.print_log("Terminated " + str(len(process_list)) + " processes")

    def __log_process_message(self, process_id, message):
        self._logger.print_log("[process: " + str(process_id) + "] " + message)