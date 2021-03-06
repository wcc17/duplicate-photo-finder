# duplicate-photo-finder
Python script that compares one set of photos to another to identify duplicates. 

 - Utilizes multiprocessing (DEFAULT PROCESS COUNT IS 3) that can be customized by user.   
 
 - Generates md5 hashes associated to filepaths for each file in folders designated by user.
 - Compares hashes to identify exact duplicates only 
 - Writes the outputs (filepaths of the duplicates, non duplicates, and skipped files) to a text file so that you can handle the duplicates how you want to (instead of relying on another program to do it)

 - Hashes for images are calculated by getting image bytes from PIL and using hashlib to calculate the hash
 - Hashes for videos are calculated by running the following command with ffmpeg. It converts video and audio to raw video and audio frames and then calculates md5 hash based on those:  
    ```ffmpeg -loglevel error -i 0329140058.mp4 -f md5 -```
    ```http://ffmpeg.org/ffmpeg-all.html#hash```  
(Let me know if you have a faster way to do this ^)

- Possible updates in future:
  - Find a faster way to hash the videos

 - Only exact copies (aside from file metadata) are calculated as duplicates
 - **No actions are taken to minimize memory usage, so keep that in mind if processing large videos

## prerequisites:
 - ```sudo apt-get install ffmpeg```
 - ```pip install PILLOW```
 - ```pip install numpy```

 - I tested on Windows using Ubuntu WSL. Running natively on Windows caused weird results with files that were created on macOS and made it difficult to retrieve files behind long directories (Windows has a short limit)

## usage: 
```sudo python main.py [-d --duplicates]=FOLDER [-o --originals]=FOLDER [-n --numprocess]=3 [-v --verbose] [-m --moviescan] [-h --help]```
 - ```duplicates```: (Required) the top level directory containing all photos that are possible duplicates of photos located in the master folder
    - to identify duplicates in the same directory, don't use the "originals" argument"
 - ```originals```:  the top level directory containing all photos that are "master" copies (you don't want to delete these)
 - ```numprocess```: Defaults to 3. the number of python processes created and run to generate hashes and then compare hashes
 - ```verbose```:    Defaults to False. Include to set to True. Will log each duplicate and nonduplicate as the processes are running (sort of breaks the progress message)
 - ```moviescan```:  Defaults to True. Include to set to False. Can be set to false to disable scanning videos, which will result in only photos being compared for duplicates
 - ```help```:       See this message

## output:
The program should not modify any media files, only the "output_files" directory that will be created in the directory main.py is run in

Up to six files will be created. Original filenames will be written to the files so that you can process them after the run however you want:  


### output_folder/duplicates.txt:  
For each media file in the "duplicates" folder whose md5 hash matches a file's md5 hash in the "originals" folder OR for each media file in the "duplicates" folder whose md5 matches another file in the "duplicates" folder, the following will be written:  
 - ```duplicates/duplicate1.png, originals/duplicate1.png```  
   
### output_folder/non-duplicates.txt:  
For each media file in the "duplicates" folder whose md5 hash doesn't match another's in the "originals" folder OR for each media file in "duplicates" folder whose md5 doesn't match another's in the "duplicates" folder, the following will be written:  
 - ```duplicates/non-duplicate.png```   
   
### output_folder/skipped_files.txt:  
For each file in the "duplicates" folder that the program could not get an md5 hash for, the following will be written. It is possible for files to be skipped in the 'originals' folder as well, but these aren't written to this file:
 - ```duplicates/skipped_files.txt```  
  
  
If these three files already exist in output_files, backups will be created of them before overwriting them in a subsequent run. These will be named:  
```output_folder/duplicates.txt.BACKUP```  
```output_folder/non-duplicates.txt.BACKUP```  
```output_folder/skipped_files.txt.BACKUP```  

## important note on output_files: 
output_files and backup output files will be modified each run. The normal output files will be backed up and then overwritten. Then the process repeats. Backup files you want to keep
output_files will be written to at the end of a run or during a run if an exception is encountered (writing during exception/shutdown is experimental/not guarenteed)

## important note on how running on a single duplicates folder works vs. running on a duplicates and originals folder
In a dual folder search, the results will only contain the first duplicate found. The program is assuming the "originals" folder will already not have duplicates

So if you have  
```duplicates_folder```  
```duplicates_folder/duplicate1.png```  
```duplicates_folder/duplicate1(copy).png```  
  
and  
  
```originals_folder```  
```originals_folder/duplicate1.png```  
```duplicates_folder/duplicate1(copy).png```  

Then the output_files/duplicates.txt will have something like:  
```duplicates_folder/duplicate1.png, originals_folder/duplicate1.png```  
```duplicates_folder/duplicate1(copy).png, originals_folder/duplicate1.png```  

Notice that even though the originals_folder had two duplicates as well, the program only matched to the first one that it found.   
To fix this, run the program on the originals_folder first, remove duplicates, then run on both duplicates and originals folders

## important note on numprocess

 - Python creates these processes IN ADDITION to the main running process (which is keeping track of numbers and what to write to files)  
 - Keep that in mind when determining how many cores/cpus you have.  
