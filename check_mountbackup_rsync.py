#!/usr/bin/env python3
'This Script was written by Bosse Klein'
import os
import subprocess

# --collector.textfile.directory=/var/lib/prometheus/textfile_collector/rsync_dc002.prom
file = '/var/lib/prometheus/textfile_collector/rsync_dc002.prom'



'''Definde Mountpoints'''
mount = []
mount = []
mountlen = len(mount)
checklist = []
failedlist = []
tmp = 0
'''Define Mountpoints'''
print("# HELP rsync successful")
print("# TYPE rsync gauge")
for i in range(0, mountlen):
    tmp = subprocess.getoutput("mount | grep {} | wc -l".format(mount[i]))
    if tmp == "1":
        checklist.append(1)
    else:
        checklist.append(2)
        failedlist.append(mount[i])


if 2 in checklist:
    print("rsync_dc002 1")
else:
    print("rsync_dc002 0")

print("# HELP failed_rsync_dir")
print("# TYPE failed_rsync_dir gauge")
for x in failedlist:
    print("failed_rync_dir{mountdir=\"" + str(x) + "\"} 1"))
