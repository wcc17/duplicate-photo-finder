# -*- coding: utf-8 -*-
from datetime import datetime

class Logger:
    def print_log(self, message):
        print("[" + str(datetime.now()) + "] " + message)