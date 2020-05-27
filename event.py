from event_type import EventType

class Event:
    
    event_type = None
    event_data = None
    event_process_id = 1

    def __init__(self, event_type, event_data, event_process_id):
        self.event_type = event_type
        self.event_data = event_data
        self.event_process_id = event_process_id