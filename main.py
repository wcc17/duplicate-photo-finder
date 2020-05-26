import os
import time
import sys
import getopt
from PIL import Image
from PIL import ImageChops
from datetime import datetime
# -*- coding: utf-8 -*-

#TODO: add to a README
#to run in terminal to print file paths with unicode characters on windows:
# chcp 65001
# set PYTHONIOENCODING=utf-8

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

OUTPUT_DIRECTORY_PATH = "output_files"
KNOWN_NON_DUPLICATES_PATH = OUTPUT_DIRECTORY_PATH + "/non-duplicates.txt"
KNOWN_DUPLICATES_PATH = OUTPUT_DIRECTORY_PATH + "/duplicates.txt"
FILES_THAT_FAILED_TO_LOAD_PATH = OUTPUT_DIRECTORY_PATH + "/files_that_failed_to_load.txt"
SKIPPED_FILES_PATH = OUTPUT_DIRECTORY_PATH + "/skipped_files.txt"
OMMITTED_KNOWN_FILES_PATH = OUTPUT_DIRECTORY_PATH + "/ommitted_known_files.txt"

_known_non_duplicates = []
_known_duplicates = []
_files_that_failed_to_load = []
_skipped_files = []
_ommitted_known_files = []
_duplicates_folder_path = None
_originals_folder_path = None
_rescan_for_duplicates = False
_omit_known_duplicates = False

def main():
    handle_args()
    create_output_folder()

    #TODO: improvements:
    #i want to show time elapsed (that will persist between exits)
    #i want to be able to spawn multiple processes by splitting the source directory up (not changing files, just splitting the work up) -- need to benchmark this though
    #clean up code to prepare for github
    #should files be written to as we go? or in batches?
    #should collect metadata on files and store in json format before processing files. That way, any file only has to be opened up if two files mode, size, file type are the same

    # _duplicates_folder_path = r"/mnt/d/Working Copy of Master Backup/Master/Christian Master Backup/Pictures and Videos/Old Pictures and Videos folder - See README inside - I want to be rid of this one"
    # _originals_folder_path=r"/mnt/d/Working Copy of Master Backup/Master/Christian Master Backup/Pictures and Videos/Master Photo Folder before icloud migration 2019/Photos Uploaded to iCloud with Correct Dates"
    #sudo python main.py --duplicates="/mnt/d/Working Copy of Master Backup/Master/Christian Master Backup/Pictures and Videos/Old Pictures and Videos folder - See README inside - I want to be rid of this one" --originals="/mnt/d/Working Copy of Master Backup/Master/Christian Master Backup/Pictures and Videos/Master Photo Folder before icloud migration 2019/Photos Uploaded to iCloud with Correct Dates"

    duplicate_folder_files_list = get_files(_duplicates_folder_path, "duplicate folder")
    originals_folder_files_list = get_files(_originals_folder_path, "originals folder")

    duplicate_folder_files_list = handle_processed_duplicates(duplicate_folder_files_list)
    originals_folder_files_list = handle_processed_originals(originals_folder_files_list)
    
    backup_old_output_files()
    process_files(duplicate_folder_files_list, originals_folder_files_list)
    write_output_for_files()

def process_files(duplicate_folder_files_list, originals_folder_files_list):
    global _rescan_for_duplicates
    global _omit_known_duplicates

    print_log("begin processing files...")

    num_processed = len(_known_non_duplicates) + len(_known_duplicates) + len(_files_that_failed_to_load) + len(_skipped_files)
    duplicate_folder_files_length = len(duplicate_folder_files_list)
    duplicate_folder_file_index = 0

    while (duplicate_folder_file_index < len(duplicate_folder_files_list)):
        print_log("Processed: " + str(num_processed) + "/" + str(duplicate_folder_files_length) + ", duplicates: " + str(len(_known_duplicates)) + ", non-duplicates: " + str(len(_known_non_duplicates)) + ", failed (not compared at all): " + str(len(_files_that_failed_to_load)) + ", skipped (not compared at all): " + str(len(_skipped_files)))
        
        duplicate_folder_file = duplicate_folder_files_list[duplicate_folder_file_index]
        duplicate_folder_file_image = get_valid_image(duplicate_folder_file)

        if(duplicate_folder_file_image == None):
            _skipped_files.append(duplicate_folder_file)
            duplicate_folder_file_index += 1
            num_processed += 1
            continue

        print_log("Processing: " + duplicate_folder_file)
        
        is_duplicate_of_original_folder_image = False
        original_folder_files_processed = 0
        for original_folder_file in originals_folder_files_list:
            is_duplicate_of_original_folder_image = compare_image_to_file(duplicate_folder_file_image, original_folder_file)

            if(is_duplicate_of_original_folder_image == True):
                print_log("Duplicate found after processing " + str(original_folder_files_processed) + " images from originals folder")
                
                if _rescan_for_duplicates == True:
                    other_duplicates = get_duplicates_after_rescan_for_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
                    duplicate_folder_files_list = [i for i in duplicate_folder_files_list if i not in other_duplicates]
                    num_processed += len(other_duplicates) 

                if _omit_known_duplicates == True:
                    handle_omit_known_duplicates(originals_folder_files_list, original_folder_file)

                break

            original_folder_files_processed += 1
            sys.stdout.write("Progress: " + str(original_folder_files_processed) + "/" + str(len(originals_folder_files_list)) + "\r")
            sys.stdout.flush()

        if(is_duplicate_of_original_folder_image == False):
            print_log("No duplicate found")
            _known_non_duplicates.append(duplicate_folder_file)
        else:
            _known_duplicates.append(duplicate_folder_file)

        num_processed += 1
        duplicate_folder_file_index += 1
    
    print_log("count of files that do not exist in original files folder: " + str(len(_known_non_duplicates)))

def get_duplicates_after_rescan_for_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file):
    other_duplicates = []

    print_log("Handling any additional duplicates")

    #get any other duplicates that may exist in duplicate_folder_files_list when compared to original_folder_file
    other_duplicates = get_other_duplicates(duplicate_folder_files_list, duplicate_folder_file_image, duplicate_folder_file)
    
    for dup in other_duplicates:
        #add other duplicates to skipped files so that we write down not to check them again
        _skipped_files.append(dup)
    
    return other_duplicates

def handle_omit_known_duplicates(originals_folder_files_list, original_folder_file):
    print_log("Removing original_folder_file so we don't check again.")

    #add the file to ommitted_known_files in case we have to reload
    _ommitted_known_files.append(original_folder_file)
    #stop looking at the original_folder_file
    originals_folder_files_list.remove(original_folder_file)

    print_log("New original_folder_files size: " + str(len(originals_folder_files_list)))
    
    return originals_folder_files_list

def get_other_duplicates(duplicate_folder_files_list, duplicate_image, duplicate_image_path):
    #if we have found a duplicate, we may have the same file multiple times in duplicate_folder_files_list
        #find all instances of "file" in duplicate_folder_files_list
        #delete each one
    #after duplicate_folder_files_list no longer contains the duplicate files, theres no chance that the copy of that file in originals_folder_files_list will need to be checked again. so we can get rid of it
    duplicates = []
    num_processed = 0

    for file_path in duplicate_folder_files_list:
        if(compare_image_to_file(duplicate_image, file_path) == True):
            duplicates.append(file_path)
            
        num_processed += 1
        sys.stdout.write("Progress: " + str(num_processed) + "/" + str(len(duplicate_folder_files_list)) + "\r")
        sys.stdout.flush()

    return duplicates

def compare_image_to_file(image_1, image_2_file_path):
    filename1, file_extension1 = os.path.splitext(image_1.filename)
    filename2, file_extension2 = os.path.splitext(image_2_file_path)
    file1_ext = file_extension1.lower()
    file2_ext = file_extension2.lower()

    #no reason to even try to compare the two files if the format is different. 
    if(file1_ext != file2_ext):
        return False

    #TODO: if size is 0, do we even bother checking?
    image_2 = get_valid_image(image_2_file_path)
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
        print_log(e)
        print_log("Exception caught comparing images (formats " + str(image_1.format) + " and " + str(image_2.format) + "). Skipping and returning False")
        return False

    if diff.getbbox():
        return False
    else:
        return True

def get_valid_image(filepath):
    try:
        image = Image.open(filepath)
        return image
    except:
        return None

def get_files(path, folder_name): 
    print_log("getting " + folder_name + " files list..") 
    file_list = []   

    #add all files to file_list                                                                                              
    for root, directories, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))
    
    #make sure all the files are open-able in the list (because windows can be dumb) and keep track of files that can't be loaded for some reason. change path if necessary
    file_list = handle_files_with_bad_paths(file_list)
    
    print_log(folder_name + " files count: " + str(len(file_list)))
    return file_list

def handle_files_with_bad_paths(file_list):
    for idx in range(len(file_list)):
        try:
            test_time = time.ctime(os.path.getctime(file_list[idx]))
        except:
            try:
                if(os.name == 'nt'):
                    #windows doesn't allow very long filepaths. we can check here to fix that and still open the file. NOTE: this works, but it doesn't seem like os.walk(path) is getting all files when running from Windows
                    #windows applies this to the beginning of the path: \\?\
                    new_path = "\\\\?\\"
                    new_path = new_path + file_list[idx]
                    test_time = time.ctime(os.path.getctime(new_path))

                    file_list[idx] = new_path
                else:
                    _files_that_failed_to_load.append(file_list[idx])
            except:
                _files_that_failed_to_load.append(file_list[idx])

    #remove the failed files, no reason to bother trying to compare them. we didn't change anything about these if we failed to open up the created time and it failed
    if(len(_files_that_failed_to_load) > 0):
        print_log("Removing " + str(len(_files_that_failed_to_load)) + " files from files_list. They will not be processed because they can't be opened")
        print_log("file_list size: " + str(len(file_list)))
        
        file_list = [i for i in file_list if i not in _files_that_failed_to_load]
        print_log("file_list size: " + str(len(file_list)))
    
    return file_list

def handle_processed_duplicates(duplicate_folder_files_list):
    print_log("sort out duplicates files that have already been marked as processed...")

    duplicate_folder_files_list = remove_paths_for_file(duplicate_folder_files_list, KNOWN_NON_DUPLICATES_PATH, _known_non_duplicates)
    duplicate_folder_files_list = remove_paths_for_file(duplicate_folder_files_list, KNOWN_DUPLICATES_PATH, _known_duplicates)
    duplicate_folder_files_list = remove_paths_for_file(duplicate_folder_files_list, FILES_THAT_FAILED_TO_LOAD_PATH, _files_that_failed_to_load)
    duplicate_folder_files_list = remove_paths_for_file(duplicate_folder_files_list, SKIPPED_FILES_PATH, _skipped_files)

    print_log("duplicate folder files count after scanning for already processed: " + str(len(duplicate_folder_files_list)))

    return duplicate_folder_files_list

def handle_processed_originals(originals_folder_files_list):
    global _rescan_for_duplicates

    if _rescan_for_duplicates == True:
        print_log("handle originals files that have already been marked as processed...")
        originals_folder_files_list = remove_paths_for_file(originals_folder_files_list, OMMITTED_KNOWN_FILES_PATH, _ommitted_known_files)
        print_log("originals folder files count after scanning for already processed: " + str(len(originals_folder_files_list)))

    return originals_folder_files_list 

def remove_paths_for_file(file_list, file_name, file_list_to_add_to):
    try:
        file_to_read = open(file_name, 'r')
        with file_to_read as fp:
            line = fp.readline()
            count = 1
            while line:
                filename = line.strip()

                if filename in file_list: file_list.remove(filename)
                file_list_to_add_to.append(filename)

                line = fp.readline()
                count += 1
        
        file_to_read.close()
        return file_list
    except:
        print_log("Couldn't open " + file_name + ", maybe it doesn't exist. Moving on")
        return file_list

def backup_old_output_files():
    print_log("backup old output files before writing output to file again...")

    known_non_duplicates_backup_path = KNOWN_NON_DUPLICATES_PATH + ".BACKUP"
    known_duplicates_backup_path = KNOWN_DUPLICATES_PATH + ".BACKUP"
    files_that_failed_to_load_backup_path = FILES_THAT_FAILED_TO_LOAD_PATH + ".BACKUP"
    skipped_files_backup_path = SKIPPED_FILES_PATH + ".BACKUP"
    ommitted_known_files_backup_path = OMMITTED_KNOWN_FILES_PATH + ".BACKUP"

    remove_file(known_non_duplicates_backup_path)
    remove_file(known_duplicates_backup_path)
    remove_file(files_that_failed_to_load_backup_path)
    remove_file(skipped_files_backup_path)
    remove_file(ommitted_known_files_backup_path)

    rename_file(KNOWN_NON_DUPLICATES_PATH, known_non_duplicates_backup_path)
    rename_file(KNOWN_DUPLICATES_PATH, known_duplicates_backup_path)
    rename_file(FILES_THAT_FAILED_TO_LOAD_PATH, files_that_failed_to_load_backup_path)
    rename_file(SKIPPED_FILES_PATH, skipped_files_backup_path)
    rename_file(OMMITTED_KNOWN_FILES_PATH, ommitted_known_files_backup_path)

def remove_file(filename):
    try:
        os.remove(filename)
    except:
        print_log("Could not remove " + filename + ", probably doesn't exist. Moving on")

def rename_file(old_file_name, new_file_name):
    try:
        os.rename(old_file_name, new_file_name)
    except:
        print_log("Could not rename " + old_file_name + ", probably doesn't exist. Moving on")

def write_output_for_files():
    write_output_for_file(KNOWN_NON_DUPLICATES_PATH, _known_non_duplicates)
    write_output_for_file(KNOWN_DUPLICATES_PATH, _known_duplicates)
    write_output_for_file(FILES_THAT_FAILED_TO_LOAD_PATH, _files_that_failed_to_load)
    write_output_for_file(SKIPPED_FILES_PATH, _skipped_files)
    write_output_for_file(OMMITTED_KNOWN_FILES_PATH, _ommitted_known_files)

def write_output_for_file(file_name, list_of_files):
    output_file = open(file_name, 'w+')
    for file in list_of_files:
        output_to_write = str(file) + "\n"
        output_file.write(output_to_write)

def handle_args():
    global _duplicates_folder_path
    global _originals_folder_path
    global _rescan_for_duplicates
    global _omit_known_duplicates

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'rOhd:o:', ['duplicates=', 'originals=', 'rescan', 'omitknown', 'help'])
    except:
        usage()

    for opt, arg in opts:
        if opt in (HELP_LONG_ARG, HELP_SHORT_ARG):
            usage()
            sys.exit(2)
        elif opt in (DUPLICATES_LONG_ARG, DUPLICATES_SHORT_ARG):
            _duplicates_folder_path = arg
        elif opt in (ORIGINALS_LONG_ARG, ORIGINALS_SHORT_ARG):
            _originals_folder_path = arg
        elif opt in (RESCAN_LONG_ARG, RESCAN_SHORT_ARG):
            _rescan_for_duplicates = True
        elif opt in (OMIT_KNOWN_LONG_ARG, OMIT_KNOWN_SHORT_ARG):
            _omit_known_duplicates = True

    if _originals_folder_path == None or _duplicates_folder_path == None:
        print("Must provide two folders. Exiting")
        sys.exit(2)

def create_output_folder():
    if not os.path.exists(OUTPUT_DIRECTORY_PATH):
        print_log("Creating output directory")
        os.makedirs(OUTPUT_DIRECTORY_PATH)

def usage():
    print("usage: sudo python main.py [-d --duplicates] [-o --originals] [-r --rescan] [-O --omitknown] [-h --help]")
    print("     duplicates: the top level directory containing all photos that are possible duplicates of photos located in the master folder")
    print("     originals: the top level directory containing all photos that are \"master\" copies (you don't want to delete these)")
    print("     rescan: NOT FULLY FUNCTIONAL: when a duplicate photo is found, do an additional scan of the \"duplicates\" folder and remove any other exact duplicates. Best when combined with --omitknown (\"-O\"). Very slow")
    print("     omitknown: NOT FULLY FUNCTIONAL: Omit the copy in the \"originals\" folder so it's not processed again. Can lead to false positives in the \"duplicates\" folder if the \"omitknown\" command isn't also used. Best when combined with --rescan (\"-r\")")
    print("     help: see this message")

def print_log(message):
    print("[" + str(datetime.now()) + "] " + message)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_log('Interrupted, writing output to files')
        write_output_for_files()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as e:
        print_log(str(e))
        print_log('Exception occurred, writing output to files')
        write_output_for_files()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
