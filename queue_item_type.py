from enum import Enum

class QueueItemType(Enum):
    DUPLICATE = 1
    NON_DUPLICATE = 2
    FAILED_TO_LOAD = 3
    SKIPPED = 4
    OMITTED_KNOWN = 5