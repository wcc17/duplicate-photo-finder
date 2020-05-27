from event_type import EventType

class Event:
    
    event_type = None
    event_string = None
    event_process_id = 1

    def __init__(self, event_type, event_string, event_process_id):
        self.event_type = event_type
        self.event_string = event_string
        self.event_process_id = event_process_id