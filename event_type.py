from enum import Enum

class EventType(Enum):
    DUPLICATE = 1
    NON_DUPLICATE = 2
    FAILED_TO_LOAD = 3
    SKIPPED = 4
    NUM_PROCESSED_CHANGED = 5
    PROCESS_DONE = 6