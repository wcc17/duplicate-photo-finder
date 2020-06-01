from multiprocessing import Pipe

class OneWayConnection:

    receiving_connection = None
    sending_connection = None

    def __init__(self):
        #If duplex is True (the default) then the pipe is bidirectional. If duplex is False then the pipe is unidirectional: conn1 can only be used for receiving messages and conn2 can only be used for sending messages.
        self.receiving_connection, self.sending_connection = Pipe(duplex = False)