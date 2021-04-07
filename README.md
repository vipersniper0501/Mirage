# Mirage
A crappy malware detection/file difference checking system.

This program was made for the 2021 KMC AFCEA SkillsUSA Programming competition.

FYI: This program does not do well with large directories such as the root drive of an OS.

## How it works

This program works by recursively scanning through a directory and collecting the last accessed
date of all of the files.
It will then wait a specified amount of time (default is 30 seconds) before scanning the same directory a second time.
After this second scan it will compare the dates from the first scan and second scan to tell if a file has changed, new date was found that wasn't in the original scan (New File was created), or if a file can not be found in the second scan where it can be found in the first (File Deleted).

NOTE: The program is prone to giving false positives when it detects that a file has a new name. It can not tell the
difference between a new file name and new file. There is currently no way to fix this without having the
program scan through each and every file and logging its contents, making the program EXTREMELEY slow and invasive to
the user.

Once one of these changes are detected it will notify the user and print in a log on the side what type of changed occurred and to where and what file it occurred on.


This program can scan the root drive, however it takes so long (for my half full one terabyte SSD drive on windows 10 took around 30 minutes) that it is impractical to use this program. The best use case for this program is to have
it monitor smaller drives or directories with far fewer files. The actual size of the files does not particularly affect
the speed of the program as the amount of files a directory contains.
