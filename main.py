# -*- coding: utf-8 -*-
import os
import sys
import getopt
import traceback
from duplicate_finder import DuplicateFinder

OUTPUT_DIRECTORY_PATH = "output_files"

DUPLICATES_LONG_ARG = "--duplicates"
DUPLICATES_SHORT_ARG = "-d"
ORIGINALS_LONG_ARG = "--originals"
ORIGINALS_SHORT_ARG = "-o"
HELP_LONG_ARG = "--help"
HELP_SHORT_ARG = "-h"
NUMPROCESS_LONG_ARG = "--numprocess"
NUMPROCESS_SHORT_ARG = "-n"
VERBOSE_LONG_ARG = "--verbose"
VERBOSE_SHORT_ARG = "-v"
MOVIESCAN_LONG_ARG = "--moviescan"
MOVIESCAN_SHORT_ARG = "-m"

duplicates_folder_path = None
originals_folder_path = None
process_count = 3
use_verbose_logging = False
should_scan_videos = False

def run():
    create_output_folder()
    handle_args()

    single_folder_dupe_search = False
    if(originals_folder_path == None):
        single_folder_dupe_search = True

    duplicate_finder = DuplicateFinder(OUTPUT_DIRECTORY_PATH, use_verbose_logging, should_scan_videos, process_count)
    duplicate_finder.execute(duplicates_folder_path, originals_folder_path, single_folder_dupe_search)

def handle_args():
    global duplicates_folder_path
    global originals_folder_path
    global process_count
    global use_verbose_logging
    global should_scan_videos

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:o:n:vm', ['duplicates=', 'originals=', 'numprocess=', 'verbose', 'moviescan', 'help'])

        for opt, arg in opts:
            if opt in (HELP_LONG_ARG, HELP_SHORT_ARG):
                usage()
                sys.exit(2)
            elif opt in (DUPLICATES_LONG_ARG, DUPLICATES_SHORT_ARG):
                duplicates_folder_path = arg
            elif opt in (ORIGINALS_LONG_ARG, ORIGINALS_SHORT_ARG):
                originals_folder_path = arg
            elif opt in (NUMPROCESS_LONG_ARG, NUMPROCESS_SHORT_ARG):
                process_count = int(arg)
            elif opt in (VERBOSE_LONG_ARG, VERBOSE_SHORT_ARG):
                use_verbose_logging = True
            elif opt in (MOVIESCAN_LONG_ARG, MOVIESCAN_SHORT_ARG):
                should_scan_videos = True
    except:
        usage()

    if duplicates_folder_path == None:
        print("Must provide at least one folder. Exiting")
        sys.exit(2)

def usage():
    print("usage: sudo python main.py [-d --duplicates]=FOLDER [-o --originals]=FOLDER [-n --numprocess]=3 [-v --verbose] [-m --moviescan] [-h --help]")
    print("     [duplicates]: the top level directory containing all photos that are possible duplicates of photos located in the originals folder")
    print("                         *to identify duplicates in the same directory, don't use the \"originals\" argument")
    print("     [originals]:  the top level directory containing all photos that are \"master\" copies (you don't want to delete these)")
    print("     [numprocess]: Defaults to 3. the number of python processes created and run to generate hashes and then compare hashes")
    print("     [verbose]:    Defaults to False. Include to set to True. Will log each duplicate and nonduplicate as the processes are running (sort of breaks the progress message)")
    print("     [moviescan]:  Defaults to False. Include to set to True. Can be set to true to enable scanning videos, which will result in only photos being compared for duplicates (slower)")
    print("     [help]:       See this message")

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
