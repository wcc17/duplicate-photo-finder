import sys
from logger import Logger
from event import Event
from event_type import EventType

class DuplicateProcessorEventHandler:

    _logger = None

    def __init__(self):
        self._logger = Logger()
    
    def handle_event(self, event, process_num_processed_list, num_processed, known_duplicates, known_non_duplicates, skipped_files, total_to_process, sub_lists, process_list, finished_process_count):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type

        if event_type == EventType.DUPLICATE:
            self.__log_process_message(event_process_id, "Duplicate found: " + event_data.filepath)
            known_duplicates.append(event_data.filepath)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.NON_DUPLICATE:
            self.__log_process_message(event_process_id, "Unique image found: " + event_data.filepath)
            known_non_duplicates.append(event_data.filepath)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.SKIPPED:
            self.__log_process_message(event_process_id, "Skipped file: " + event_data.filepath)
            skipped_files.append(event_data.filepath)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.PROCESS_DONE:
            finished_process_count += 1

        self.__write_progress_to_console(num_processed, total_to_process, process_num_processed_list, sub_lists, process_list)
        return (num_processed, finished_process_count)

    def __write_progress_to_console(self, num_processed, total_to_process, process_num_processed_list, sub_lists, process_list):
        #overall_percentage_str = self.__get_progress_percentage_str(num_processed, total_to_process)
        output_str = "Overall Progress: " + str(num_processed) + "/" + str(total_to_process) + " " #+ overall_percentage_str + "%" TODO:

        for i in range(0, len(process_num_processed_list)):
            #percentage_str = self.__get_progress_percentage_str(process_num_processed_list[i], len(sub_lists[i]))
            is_running_str = "Running" if self.__is_process_running(process_list[i]) else "Stopped"
            output_str += ",    Process " + str(i+1) + "(" + is_running_str + ")" + ": " + str(process_num_processed_list[i]) + "/" + str(len(sub_lists[i]))  + " " # + percentage_str + "%" TODO

        sys.stdout.write(output_str + "\r")
        sys.stdout.flush()
    
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