from multiprocessing import Pipe

class TwoWayConnection:

    child_connection = None
    parent_connection = None

    def __init__(self):
        self.child_connection, self.parent_connection = Pipe(duplex = True)