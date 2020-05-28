from enum import Enum

class EventType(Enum):
    DUPLICATE = 1
    NON_DUPLICATE = 2
    FAILED_TO_LOAD = 3
    SKIPPED = 4
    PROCESS_DONE = 5
    FILE_HASHED = 6
    SKIPPED_FILE_HASH = 7