import sys
from logger import Logger
from event import Event
from event_type import EventType
from event_handler import EventHandler

class HashEventHandler(EventHandler):

    def __init__(self, use_verbose_logging):
        super().__init__(use_verbose_logging)

    def handle_event(self, event, num_processed_by_process_list,  num_processed, total_to_process, image_models, skipped_files, append_to_be_skipped):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type
        
        if event_type == EventType.FILE_HASHED:
            image_models.append(event_data)
            num_processed += 1
            num_processed_by_process_list[event_process_id-1] += 1

        elif event_type == EventType.SKIPPED_FILE_HASH:
            if append_to_be_skipped == True:
                #we want to skip any file that doesn't load properly, but we only want to write skipped_files from the "duplicates" directory to skipped_files.txt
                skipped_files.append(event_data)
            num_processed += 1
            num_processed_by_process_list[event_process_id-1] += 1

        return num_processed