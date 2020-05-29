import sys
from logger import Logger
from event import Event
from event_type import EventType

class HashEventHandler:

    _logger = None

    def __init__(self):
        self._logger = Logger()

    def handle_event(self, image_models, skipped_files, sub_lists, event, num_processed, process_num_processed_list, finished_process_count, total_to_process, process_list):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type
        
        if event_type == EventType.FILE_HASHED:
            image_models.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.SKIPPED_FILE_HASH:
            skipped_files.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1
            #TODO: increase a "files_removed" variable and then log the results outside of this method 

        elif event_type == EventType.PROCESS_DONE:
            finished_process_count += 1

        self.__write_progress_to_console(num_processed, total_to_process, process_num_processed_list, sub_lists, process_list)
        return (num_processed, finished_process_count)

    def __write_progress_to_console(self, num_processed, total_to_process, process_num_processed_list, sub_lists, process_list):
        #overall_percentage_str = self.__get_progress_percentage_str(num_processed, total_to_process)
        output_str = "Overall Progress: " + str(num_processed) + "/" + str(total_to_process) + " " # + overall_percentage_str + "%" TODO

        for i in range(0, len(process_num_processed_list)):
            #percentage_str = self.__get_progress_percentage_str(process_num_processed_list[i], len(sub_lists[i]))
            is_running_str = "Running" if self.__is_process_running(process_list[i]) else "Stopped"
            output_str += ",    Process " + str(i+1) + "(" + is_running_str + ")" + ": " + str(process_num_processed_list[i]) + "/" + str(len(sub_lists[i]))  + " " # + percentage_str + "%" TODO

        sys.stdout.write(output_str + "\r")
        sys.stdout.flush()

    #TODO: a ton of overlap with duplicate_processor_event_handler
    def __get_progress_percentage_str(self, progress, total): 
        percentage = round((float(progress) / float(total)), 3)
        return str(percentage)

    def __some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        return False

    def __is_process_running(self, process):
        return process.is_alive()

    def __log_process_message(self, process_id, message):
        self._logger.print_log("[process: " + str(process_id) + "] " + message)