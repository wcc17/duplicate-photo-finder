from logger import Logger
import sys

class EventHandler:

    _use_verbose_logging = False

    def __init__(self, use_verbose_logging):
        self._logger = Logger()
        self._use_verbose_logging = use_verbose_logging

    def _log_process_message(self, process_id, message):
        if self._use_verbose_logging:
            self._logger.print_log("[process: " + str(process_id) + "] " + message)