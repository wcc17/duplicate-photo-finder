# duplicate-photo-finder
Python script that compares one set of photos to another to identify duplicates. Can be run with multiple processes

### usage: 
```sudo python main.py [-d --duplicates] [-o --originals] [-h --help]```
 - ```duplicates```: the top level directory containing all photos that are possible duplicates of photos located in the master folder
 - - - *to identify duplicates in the same directory, don't use the "originals" argument"
 - ```originals```: the top level directory containing all photos that are "master" copies (you don't want to delete these)
 - ```help```: see this message

### NOTES
In a dual folder search, the results will only contain the first duplicate found. The program is assuming the "originals" folder will already not have duplicates