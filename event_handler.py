from logger import Logger
import sys

class EventHandler:

    _use_verbose_logging = False

    def __init__(self, use_verbose_logging):
        self._logger = Logger()
        self._use_verbose_logging = use_verbose_logging

    def _write_progress_to_console(self, num_processed, total_to_process):
        output_str = "Progress: " + str(num_processed) + "/" + str(total_to_process) + " "
        sys.stdout.write(output_str + "\r")
        sys.stdout.flush()

    def _log_process_message(self, process_id, message):
        if self._use_verbose_logging:
            self._logger.print_log("[process: " + str(process_id) + "] " + message)