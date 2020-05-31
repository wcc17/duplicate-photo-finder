import sys
from logger import Logger
from event import Event
from event_type import EventType
from event_handler import EventHandler

class DuplicateProcessorEventHandler(EventHandler):

    _logger = None

    def __init__(self, use_verbose_logging):
        super().__init__(use_verbose_logging)
    
    def handle_event(self, event, num_processed, process_num_processed_list, finished_process_count, total_to_process, process_list, sub_lists, known_duplicates, known_non_duplicates, skipped_files, single_folder_dupe_search):
        event_process_id = event.event_process_id
        event_data = event.event_data
        event_type = event.event_type

        if event_type == EventType.DUPLICATE:
            duplicate_result = event_data

            if single_folder_dupe_search:
                if any(duplicate_result.equals(other_duplicate) for other_duplicate in known_duplicates):
                    self._log_process_message(event_process_id, "Duplicate found, but it was already reported: " + event_data.get_print_str())
                else:
                    self._log_process_message(event_process_id, "Duplicate found: " + event_data.get_print_str())
                    known_duplicates.append(event_data.get_print_str())
            else:
                self._log_process_message(event_process_id, "Duplicate found: " + event_data.get_print_str())
                known_duplicates.append(event_data.get_print_str())

            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.NON_DUPLICATE:
            self._log_process_message(event_process_id, "Unique image found: " + event_data.filepath)
            known_non_duplicates.append(event_data.filepath)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.SKIPPED:
            self._log_process_message(event_process_id, "Skipped file: " + event_data.filepath)
            skipped_files.append(event_data.filepath)
            process_num_processed_list[event_process_id-1] += 1
            num_processed += 1

        elif event_type == EventType.PROCESS_DONE:
            finished_process_count += 1

        self._write_progress_to_console(num_processed, total_to_process, process_num_processed_list, sub_lists, process_list, finished_process_count) # TODO: why is this in event_handler and not in BaseProcessor?
        return (num_processed, finished_process_count)