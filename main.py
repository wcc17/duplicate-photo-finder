# -*- coding: utf-8 -*-
import os
import sys
import getopt
from duplicate_processor import DuplicateProcessor

OUTPUT_DIRECTORY_PATH = "output_files"

DUPLICATES_LONG_ARG = "--duplicates"
DUPLICATES_SHORT_ARG = "-d"
ORIGINALS_LONG_ARG = "--originals"
ORIGINALS_SHORT_ARG = "-o"
RESCAN_LONG_ARG = "--rescan"
RESCAN_SHORT_ARG = "-r"
OMIT_KNOWN_LONG_ARG = "--omitknown"
OMIT_KNOWN_SHORT_ARG = "-O"
HELP_LONG_ARG = "--help"
HELP_SHORT_ARG = "-h"

duplicates_folder_path = None
originals_folder_path = None
rescan_for_duplicates = False
omit_known_duplicates = False

def run():
    create_output_folder()
    handle_args()

    process_count = 4 #TODO: should be an argument to the program
    duplicate_processer = DuplicateProcessor(OUTPUT_DIRECTORY_PATH, duplicates_folder_path, originals_folder_path, rescan_for_duplicates, omit_known_duplicates, process_count)
    duplicate_processer.execute()

def handle_args():
    global duplicates_folder_path
    global originals_folder_path
    global rescan_for_duplicates
    global omit_known_duplicates

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'rOhd:o:', ['duplicates=', 'originals=', 'rescan', 'omitknown', 'help'])
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
        elif opt in (RESCAN_LONG_ARG, RESCAN_SHORT_ARG):
            rescan_for_duplicates = True
        elif opt in (OMIT_KNOWN_LONG_ARG, OMIT_KNOWN_SHORT_ARG):
            omit_known_duplicates = True

    if originals_folder_path == None or duplicates_folder_path == None:
        print("Must provide two folders. Exiting")
        sys.exit(2)

def usage():
    print("usage: sudo python main.py [-d --duplicates] [-o --originals] [-r --rescan] [-O --omitknown] [-h --help]")
    print("     duplicates: the top level directory containing all photos that are possible duplicates of photos located in the master folder")
    print("     originals: the top level directory containing all photos that are \"master\" copies (you don't want to delete these)")
    print("     rescan: NOT FULLY FUNCTIONAL: when a duplicate photo is found, do an additional scan of the \"duplicates\" folder and remove any other exact duplicates. Best when combined with --omitknown (\"-O\"). Very slow")
    print("     omitknown: NOT FULLY FUNCTIONAL: Omit the copy in the \"originals\" folder so it's not processed again. Can lead to false positives in the \"duplicates\" folder if the \"omitknown\" command isn't also used. Best when combined with --rescan (\"-r\")")
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
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    main()
