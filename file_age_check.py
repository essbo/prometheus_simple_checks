#!/usr/bin/env python3
'This Script was written by Bosse Klein'

# --collector.textfile.directory=/var/lib/prometheus/textfile_collector/file_age_check_backup.lg.spnoc

import argparse
import os
import time

'''Define the Argparse Arguements'''
parser = argparse.ArgumentParser(description="Process command line arguments.")
parser.add_argument("path", type=str, help="Runs the Script inside the choosen directory")
parser.add_argument("file", type=str, help="The Script will look for a specific filetype")
parser.add_argument("time", type=str, help="The Script will look for everything above the given time")
parser.add_argument("--mdir", action='store_true', help="Selects sub-directories inside the choosen path")

args = parser.parse_args()
path = args.path
file = args.file
timer = args.time
if args.mdir:
    mdir = 1
else:
    mdir = 0
'''Define List'''
fileinpath = []
filelist = []
dirlist = [f.name for f in os.scandir(path) if f.is_dir()]
dirpath = [f.path for f in os.scandir(path) if f.is_dir()]
'''Define Functions'''
l = 0
timelist = {}


def func_main(path, file):
    '''Create Dicts for each Folder'''
    if mdir == 1:
        if os.path.isdir(path):
            dirdict = {}
            buffer = []
            i = 0
            z = len(dirlist)
            for x in range(0, z):
                dirdict[dirlist[x]] = 0
            while i < z:
                buffer = fileAge(dirpath[i], file)
                if any(File.endswith(file) for File in os.listdir(dirpath[i])):
                    dirdict[dirlist[i]] = buffer
                    i += 1
                else:
                    i += 1
                if i == z:
                    return dirdict
    else:
        return fileAge(path, file)


'''Create Dict that contains file-names and the age of the file'''

def fileAge(path, file):
    filedict = {}
    i = 0
    filelist = [f.name for f in os.scandir(path) if f.is_file()]
    x = len(filelist)
    while x > i:
        if mdir == 0:
            filepath = "{}{}".format(path, filelist[i])
        else:
            filepath = "{}/{}".format(path, filelist[i])
        if filepath.endswith(file):
            filetime = time.time() - os.path.getmtime(filepath)
            filedict[filelist[i]] = filetime
            i += 1
        else:
            i += 1
        if i == x:
            return filedict


'''simple check of a given value'''


def agecheck(filedict, timer):
    f = 1 + len(filedict)
    i = 1
    brk = False
    for k, v in filedict.items():
        if v == 0:
            f -= 1
            brk = False
        elif type(v) is dict and brk is False:
            for nk, nv in v.items():
                if (min(v.values())) > float(timer) and i < f:
                    timelist[k] = (min(v, key=v.get))
                    brk = True
                    i += 1
                    if i > f:
                        return timelist
                elif i > f and brk is False:
                    return timelist
        elif mdir == 0:
            if (min(filedict.values())) > float(timer):
                return (min(filedict, key=filedict.get))
        elif f > i and timelist is not None:
            return timelist



fac = agecheck(func_main(path, file), timer)

'''Print the Prometheus Metrics'''

if mdir == 0:
    print("# HELP file_age_check Checks if a file in the choosen direcotry is older than " + timer + " seconds")
    print("# TYPE file_age_check gauge")
    if fac is not None:
        print("file_age_check" + path.rstrip("/").replace(" ", "_").replace("/", "_") + " 1")
    else:
        print("file_age_check" + path.rstrip("/").replace(" ", "_").replace("/", "_") + " 0")
    if fac is not None:
        print("# HELP faulty_file collects the youngest files inside a choosen directory that are oldern than " + timer + " seconds")
        print("# TYPE file_age_check counter")
        print("faulty_file" + path.replace(" ", "_").replace("/", "_") + fac.replace(" ", "_").replace("-", "_").replace(".", "_"))


if mdir == 1:
    print("# HELP file_age_check Checks if a file in the choosen direcotry is older than " + timer + " seconds")
    print("# TYPE file_age_check gauge")
    if fac is not None:
        print("file_age_check" + path.rstrip("/").replace(" ", "_").replace("/", "_") + " 1")
    else:
        print("file_age_check" + path.rstrip("/").replace(" ", "_").replace("/", "_") + " 0")

    print("# HELP faulty_file collects the youngest files inside a choosen directory that are oldern than " + timer + " seconds")
    print("# TYPE file_age_check counter")
    if fac is not None:
        for k, v in fac.items():

            print("faulty_file" + path.replace(" ", "_").replace("/", "_") + k.replace(" ", "_").replace("/", "_").replace("-", "_") + "_" + v.replace(" ", "_").replace("/", "_").replace(".", "_").replace("-", "_"))
