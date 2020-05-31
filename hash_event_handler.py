import sys
from logger import Logger
from event import Event
from event_type import EventType
from event_handler import EventHandler

class HashEventHandler(EventHandler):

    def __init__(self, use_verbose_logging):
        super().__init__(use_verbose_logging)

    def handle_event(self, event, num_processed, process_num_processed_list, finished_process_count, total_to_process, process_list, sub_lists, image_models, skipped_files, append_to_be_skipped):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type
        
        if event_type == EventType.FILE_HASHED:
            image_models.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.SKIPPED_FILE_HASH:
            if append_to_be_skipped == True:
                #we want to skip any file that doesn't load properly, but we only want to write skipped_files from the "duplicates" directory to skipped_files.txt
                skipped_files.append(event_data)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.PROCESS_DONE:
            finished_process_count += 1

        self._write_progress_to_console(num_processed, total_to_process, process_num_processed_list, sub_lists, process_list, finished_process_count)
        return (num_processed, finished_process_count)