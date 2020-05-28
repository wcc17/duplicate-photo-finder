# -*- coding: utf-8 -*-
import os
import sys
import getopt
import traceback
from duplicate_processor import DuplicateProcessor

OUTPUT_DIRECTORY_PATH = "output_files"

DUPLICATES_LONG_ARG = "--duplicates"
DUPLICATES_SHORT_ARG = "-d"
ORIGINALS_LONG_ARG = "--originals"
ORIGINALS_SHORT_ARG = "-o"
HELP_LONG_ARG = "--help"
HELP_SHORT_ARG = "-h"

duplicates_folder_path = None
originals_folder_path = None

def run():
    create_output_folder()
    handle_args()

    process_count = 4 #TODO: should be an argument to the program
    duplicate_processer = DuplicateProcessor(OUTPUT_DIRECTORY_PATH, duplicates_folder_path, originals_folder_path, process_count)
    duplicate_processer.execute()

def handle_args():
    global duplicates_folder_path
    global originals_folder_path

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:o:', ['duplicates=', 'originals=', 'help'])
    except:
        usage()

    for opt, arg in opts:
        if opt in (HELP_LONG_ARG, HELP_SHORT_ARG):
            usage()
            sys.exit(2)
        elif opt in (DUPLICATES_LONG_ARG, DUPLICATES_SHORT_ARG):
            duplicates_folder_path = arg
        elif opt in (ORIGINALS_LONG_ARG, ORIGINALS_SHORT_ARG):
            originals_folder_path = arg

    if originals_folder_path == None or duplicates_folder_path == None:
        print("Must provide two folders. Exiting")
        sys.exit(2)

def usage():
    print("usage: sudo python main.py [-d --duplicates] [-o --originals] [-r --rescan] [-O --omitknown] [-h --help]")
    print("     duplicates: the top level directory containing all photos that are possible duplicates of photos located in the master folder")
    print("     originals: the top level directory containing all photos that are \"master\" copies (you don't want to delete these)")
    print("     help: see this message")

def create_output_folder():
    if not os.path.exists(OUTPUT_DIRECTORY_PATH):
        print("Creating output directory")
        os.makedirs(OUTPUT_DIRECTORY_PATH)

def main():
    try:
        run()
    except Exception as e:
        print(e) #don't use logger for this
        traceback.print_exc()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    main()
