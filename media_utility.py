import os
import mimetypes
import hashlib
from PIL import Image
from PIL import ImageChops
from logger import Logger
from media_model import MediaModel
import subprocess
import re

class MediaUtility:

    _logger = None
    _use_verbose_logging = False

    def __init__(self, use_verbose_logging):
        self._logger = Logger()
        self._use_verbose_logging = use_verbose_logging
        mimetypes.init()

    def is_image_file(self, filepath):
        return self.__is_media_file(filepath, 'image')

    def is_video_file(self, filepath):
        return self.__is_media_file(filepath, 'video')

    def get_media_model_for_image(self, filepath):
        image = self.__get_valid_image(filepath)

        if image == None:
            return None
        else:
            hash = self.__get_image_hash(image)
            if not hash == None:
                image_model = MediaModel(filepath, hash.hexdigest())
                return image_model
            
            return None

    def get_media_model_for_video(self, filepath):
        try:
            hash = self.__get_ffmpeg_video_hash(filepath)

            if(self.__is_valid_md5(hash)):
                video_model = MediaModel(filepath, hash)
                return video_model
            
            return None
        except Exception as e:
            self.__log_message("Exception encountered loading media model for video" + filepath)
            self.__log_message(str(e))
            return None

    def __is_media_file(self, filepath, media_type_str):
        mimestart = mimetypes.guess_type(filepath)[0]

        if mimestart != None:
            mimestart = mimestart.split('/')[0]

            if mimestart == media_type_str:
                return True
            
        return False

    def __get_valid_image(self, filepath):
        try:
            image = Image.open(filepath)
            return image
        except Exception as e:
            self.__log_message("Exception encountered loading image with PIL" + filepath)
            self.__log_message(str(e))
            return None

    def __get_ffmpeg_video_hash(self, filepath):
        # couldn't really find a good way to use ffmpeg python bindings, had to resort to using ffmpeg in subprocess
        # ffmpeg -loglevel error -i 0329140058.mp4 -f md5 -
        # 'MD5=0d67be762adf54a8b690f62d293f017b'
        command_str = 'ffmpeg -loglevel error -i \"' + filepath + '\" -f md5 -'
        process = subprocess.Popen([command_str], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        hash = None
        if process.returncode == 0:
            hash = str(stdout)                  # "'bMD5=0d67be762adf54a8b690f62d293f017b\\n'"
            hash = hash.split("=")[1]           # "ded0a1af9310f7645cd3fdb447b4ec23\\n'"
            hash = hash.replace("\\n'", "")     # 'ded0a1af9310f7645cd3fdb447b4ec23'
        
        return hash

    def __get_image_hash(self, image):
        try:
            hash = hashlib.md5(image.tobytes())
            return hash
        except Exception as e:
            self.__log_message("Exception encountered getting hash for image")
            self.__log_message(str(e))
            return None

    def __is_valid_md5(self, hash):
        matches = re.findall(r"([a-fA-F\d]{32})", hash)
        if(len(matches) > 0):
            return True
        
        return False

    def __log_message(self, message):
        if self._use_verbose_logging:
            self._logger.print_log(message)