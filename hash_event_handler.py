import sys
from logger import Logger
from event import Event
from event_type import EventType
from event_handler import EventHandler

class HashEventHandler(EventHandler):

    def __init__(self, use_verbose_logging):
        super().__init__(use_verbose_logging)

    def handle_event(self, event, num_processed, process_num_processed_list, finished_process_count, total_to_process, process_list, image_models, skipped_files, sub_lists):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type
        
        if event_type == EventType.FILE_HASHED:
            image_models.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.SKIPPED_FILE_HASH:
            skipped_files.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1
            #TODO: increase a "files_removed" variable and then log the results outside of this method 

        elif event_type == EventType.PROCESS_DONE:
            finished_process_count += 1

        self._write_progress_to_console(num_processed, total_to_process, process_num_processed_list, sub_lists, process_list)
        return (num_processed, finished_process_count)