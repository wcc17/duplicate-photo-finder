from multiprocessing import Process

class BaseWorker(Process):

    process_id = 0
    file_list = []
    _queue = None
    _connection = None

    def __init__(self, process_id, file_list, queue, _connection):
        super(BaseWorker, self).__init__()

        self.process_id = process_id
        self.file_list = file_list
        self._queue = queue
        self._connection = _connection

    def _clear_already_processed_files(self, files_to_remove):
        try:
            self.file_list = [file for file in self.file_list if file not in files_to_remove]
        except:
            pass

    def _redisperse_message_received(self):
        if self._connection.poll():
            message = self._connection.recv()
            if message == "REDISPERSE":
                return True

        return False

    def _send_filelist_to_main_process(self):
        self._connection.send(self.file_list)

