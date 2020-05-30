class DuplicateResultModel:

    file_path1 = None
    file_path2 = None

    def __init__(self, file_path1, file_path2):
            self.file_path1 = file_path1
            self.file_path2 = file_path2

    def equals(self, other):
        if self.get_print_str() == other or self._get_print_str_reverse() == other:
            return True
            
        return False

    def get_print_str(self):
        return (self.file_path1 + ", " + self.file_path2)

    def _get_print_str_reverse(self):
        return (self.file_path2 + ", " + self.file_path1)