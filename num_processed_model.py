class NumProcessedModel:

    num_processed = 0
    total_to_process = 0

    def __init__(self, num_processed, total_to_process):
        self.num_processed = num_processed
        self.total_to_process = total_to_process

    def increment_num_processed(self):
        self.num_processed += 1