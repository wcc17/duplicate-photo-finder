from processor_file_handler import ProcessorFileHandler
from hash_processor import HashProcessor
from duplicate_processor import DuplicateProcessor
from logger import Logger

class DuplicateFinder:

    _logger = None
    _file_handler = None

    _duplicate_hash_processor = None
    _originals_hash_processor = None
    _duplicate_processor = None

    _known_non_duplicates = []
    _known_duplicates = []
    _skipped_files = []

    def __init__(self, output_file_path, use_verbose_logging, should_scan_videos, process_count):
        self._file_handler = ProcessorFileHandler(output_file_path)

        self._logger = Logger()
        self._duplicate_hash_processor = HashProcessor(self._file_handler, use_verbose_logging, should_scan_videos, process_count)
        self._originals_hash_processor = HashProcessor(self._file_handler, use_verbose_logging, should_scan_videos, process_count)
        self._duplicate_processor = DuplicateProcessor(self._file_handler, use_verbose_logging, process_count)

    def execute(self, duplicates_folder_path, originals_folder_path, single_folder_dupe_search):
        
        try:
            potential_duplicate_image_models = []
            originals_folder_image_models = []

            potential_duplicate_image_models = self._duplicate_hash_processor.process(duplicates_folder_path, "duplicates folder", self._skipped_files, True)
            
            if(not single_folder_dupe_search):
                originals_folder_image_models = self._originals_hash_processor.process(originals_folder_path, "originals folder", self._skipped_files, False)
            else:
                originals_folder_image_models = potential_duplicate_image_models

            self._duplicate_processor.process(potential_duplicate_image_models, originals_folder_image_models, self._known_non_duplicates, self._known_duplicates, self._skipped_files, single_folder_dupe_search)

        except KeyboardInterrupt:
            self._logger.print_log('Interrupted, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._skipped_files)
            raise
        except Exception:
            self._logger.print_log('Exception occurred, writing output to files')
            self._file_handler.write_output_for_files(self._known_non_duplicates, self._known_duplicates, self._skipped_files)
            raise
