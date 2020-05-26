# duplicate-photo-finder
Python script that compares one set of photos to another to identify duplicates. Can be run with multiple processes

### To run in command prompt to print file paths with unicode characters on windows:
```
chcp 65001
set PYTHONIOENCODING=utf-8
```

### usage: 
```sudo python main.py [-d --duplicates] [-o --originals] [-r --rescan] [-O --omitknown] [-h --help]```
 - ```duplicates```: the top level directory containing all photos that are possible duplicates of photos located in the master folder
 - ```originals```: the top level directory containing all photos that are "master" copies (you don't want to delete these)
 - ```rescan```: NOT FULLY FUNCTIONAL: when a duplicate photo is found, do an additional scan of the "duplicates" folder and remove any other exact duplicates. Best when combined with --omitknown ("-O"). Very slow
 - ```omitknown```: NOT FULLY FUNCTIONAL: Omit the copy in the "originals" folder so it's not processed again. Can lead to false positives in the "duplicates" folder if the "omitknown" command isn't also used. Best when combined with --rescan ("-r")
 - ```help```: see this message
