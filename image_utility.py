import os
from PIL import Image
from PIL import ImageChops
from logger import Logger

class ImageUtility:

    _logger = None

    def __init__(self):
        self._logger = Logger()

    def compare_image_to_file(self, image_1, image_2_file_path):
        filename1, file_extension1 = os.path.splitext(image_1.filename)
        filename2, file_extension2 = os.path.splitext(image_2_file_path)
        file1_ext = file_extension1.lower()
        file2_ext = file_extension2.lower()

        #no reason to even try to compare the two files if the format is different. 
        if(file1_ext != file2_ext):
            return False

        #TODO: if size is 0, do we even bother checking?
        image_2 = self.get_valid_image(image_2_file_path)
        if(image_2 == None):
            return False

        if(image_1.mode != image_2.mode):
            return False

        if(image_1.height != image_2.height):
            return False

        if(image_1.width != image_2.width):
            return False

        try:
            diff = ImageChops.difference(image_1, image_2)
        except Exception as e:
            self._logger.print_log(str(e))
            self._logger.print_log("Exception caught comparing images (formats " + str(image_1.format) + " and " + str(image_2.format) + "). Skipping and returning False")
            return False

        if diff.getbbox():
            return False
        else:
            return True

    def get_valid_image(self, filepath):
        try:
            image = Image.open(filepath)
            return image
        except:
            return None