# Mirage
A crappy malware detection/file difference checking system.

This program was made for the 2021 SkillsUSA Programming competition.

FYI: This program does not do well with large directories such as the root drive of an OS.

## How it works

This program works by recursively scanning through a directory and creating a hash of all of the files.
It will then wait a specified amount of time (default is 30 seconds) before scanning the same directory a second time.
After this second scan it will compare the hashes from the first scan and second scan to tell if a hash has changed (File Change), new hash had generated that wasn't in the original scan (New File was created), or if a hash was deleted in the second scan where it can be found in the first (File Deleted).
Once one of these changes are detected it will notify the user and print in a log on the side what type of changed occurred and to where and what file it occurred on.

