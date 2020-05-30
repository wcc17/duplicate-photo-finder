from logger import Logger
import sys

class EventHandler:

    _use_verbose_logging = False

    def __init__(self, use_verbose_logging):
        self._logger = Logger()
        self._use_verbose_logging = use_verbose_logging

    def _write_progress_to_console(self, num_processed, total_to_process, process_num_processed_list, sub_lists, process_list):
        #overall_percentage_str = self.__get_progress_percentage_str(num_processed, total_to_process)
        output_str = "Overall Progress: " + str(num_processed) + "/" + str(total_to_process) + " " #+ overall_percentage_str + "%" TODO:

        for i in range(0, len(process_num_processed_list)):
            #percentage_str = self.__get_progress_percentage_str(process_num_processed_list[i], len(sub_lists[i]))
            is_running_str = "Running" if self._is_process_running(process_list[i]) else "Stopped"
            output_str += ",    Process " + str(i+1) + "(" + is_running_str + ")" + ": " + str(process_num_processed_list[i]) + "/" + str(len(sub_lists[i]))  + " " # + percentage_str + "%" TODO

        sys.stdout.write(output_str + "\r")
        sys.stdout.flush()
    
    def _get_progress_percentage_str(self, progress, total): 
        percentage = round((float(progress) / float(total)), 3)
        return str(percentage)

    def _some_process_is_alive(self, process_list):
        for process in process_list:
            if process.is_alive():
                return True
        return False

    def _is_process_running(self, process):
        return process.is_alive()

    def _log_process_message(self, process_id, message):
        if self._use_verbose_logging:
            self._logger.print_log("[process: " + str(process_id) + "] " + message)