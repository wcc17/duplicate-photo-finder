from multiprocessing import Process
from logger import Logger

class BaseWorker(Process):

    process_id = 0
    file_list = []
    _queue = None
    _connection = None
    _use_verbose_logging = False
    _logger = None

    def __init__(self, process_id, file_list, queue, _connection, use_verbose_logging):
        super(BaseWorker, self).__init__()

        self.process_id = process_id
        self.file_list = file_list
        self._queue = queue
        self._connection = _connection
        self._use_verbose_logging = use_verbose_logging
        self._logger = Logger()

    def _clear_already_processed_files(self, files_to_remove):
        try:
            for file in files_to_remove:
                self.file_list.remove(file)
        except ValueError:
            pass

    def _redisperse_message_received(self):
        if self._connection.poll():
            message = self._connection.recv()
            if message == "REDISPERSE":
                self._connection.close()
                return True

        return False

    def _print_verbose(self, message):
        if self._use_verbose_logging:
            self._logger.print_log("Process " + str(self.process_id) + " " + message)
    