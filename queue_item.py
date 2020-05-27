from queue_item_type import QueueItemType

class QueueItem:
    queue_item_type = None
    queue_item_string = None

    def __init__(self, queue_item_type, queue_item_string):
        self.queue_item_type = queue_item_type
        self.queue_item_string = queue_item_string