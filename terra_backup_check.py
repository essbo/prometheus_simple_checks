#!/usr/bin/env python3
# This script was written by Marc-Daniell Hess - Securepoint GmbH
# This script was editet to fit into prometheus by Bosse Klein

file = '/var/lib/prometheus/textfile_collector/terra_backup_check.prom'

import re
from datetime import datetime
import argparse
import xml.etree.ElementTree as ET
import subprocess

'''construct the argument parser'''
ap = argparse.ArgumentParser()

'''add the available arguments to the parser'''

ap.add_argument("-j",
                "--job",
                required=False,
                type=str,
                help="Name the jobname to collect data from. Usally this job is called 'daily'"
                )

ap.add_argument("-m",
                "--max-age",
                required=True,
                type=int,
                help="define the time in hours within which the backup must have been performed successfully"
                )

ap.add_argument("--custompath",
                required=False,
                type=str, 
                help="define a complete custom path. Has to point to the BUAgent directory"
                )

ap.add_argument("-r",
                "--restart",
                required=False,
                action='store_true',
                help="restart the BUAgent and VVAgent if the last backup was not successful"
                )

args = ap.parse_args()

'''create the actual datetime'''
now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

'''custom config parser'''
COMMENT_CHAR = '#'
OPTION_CHAR = ' '

'''parse the config file'''


def parse_config(filename):
    options = []
    f = open(filename)
    for line in f:
        if OPTION_CHAR in line:
            option = line.split(OPTION_CHAR, -1)
            options.append(option)
    f.close()
    return options


'''calculate the hours between the last backup and the actual time'''


def hours_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%dT%H:%M:%S")
    d2 = datetime.strptime(d2, "%Y-%m-%dT%H:%M:%S")
    difference = d1 - d2
    seconds_in_day = 24 * 60 * 60
    total_seconds = divmod(difference.days * seconds_in_day + difference.seconds, 60)[0]
    return (total_seconds / 60)


'''construct the full-path of the backupstatus.xml file'''
if args.job:
    if args.custompath:
        path = args.custompath + args.job + "/BackupStatus.xml"
    else:
        path = "/opt/BUAgent/" + args.job + "/BackupStatus.xml"
else:
    if args.custompath:
        path = args.custompath
        options = parse_config(path + '/Schedule.cfg')
        jobs = options[16][3]
        path = path + jobs + "/BackupStatus.xml"
    else:
        try:
            options = parse_config('/opt/BUAgent/Schedule.cfg')
            jobs = options[16][3]
            path = '/opt/BUAgent/' + jobs + '/BackupStatus.xml'
        except OSError:
            options = parse_config('/data/opt/BUAgent/Schedule.cfg')
            jobs = options[16][3]
            path = '/data/opt/BUAgent/' + jobs + '/BackupStatus.xml'
if args.restart:
    restart = True
else:
    restart = False

'''check if a custompath is defined'''


'''parse XML file and extract useful stuff'''
tree = ET.parse(path)
root = tree.getroot()
for child in root:
    if "result" in child.tag:
        jobresult = child.text
    if "dateTime" in child.tag:
        jobtime = child.text
        jobtime = re.split('\.', child.text)
        jobtime.pop()


'''Print Metrics'''
hours_between_jobs = hours_between(now, jobtime[0])

if hours_between_jobs < args.max_age and jobresult == "COMPLETED":
    '''LAST Backup was SUCCSESSFULL'''
    print("# HELP terra_backup_check Checks if the last Terra Backup was successful ")
    print("# TYPE terra_backup_check gauge")
    print("terra_backup_check 0")
elif hours_between_jobs < args.max_age and jobresult == "UNKNOWN":
    '''LAST Backup is Status UNKNOWN'''
    print("# HELP terra_backup_check Checks if the last Terra Backup was successful ")
    print("# TYPE terra_backup_check gauge")
    print("terra_backup_check 1")
    if restart:
        try:
            subprocess.run("systemctl restart vvagent", shell=True)
            subprocess.run("ps faux | grep -i BUAGent | grep -v color | awk '{ print $2 }' | xargs kill -9", shell=True)
            subprocess.run("systemctl restart vvagent", shell=True)
        except subprocess.SubprocessError:
            subprocess.run("systemctl restart BUAgent", shell=True)
            subprocess.run("ps faux | grep -i BUAGent | grep -v color | awk '{ print $2 }' | xargs kill -9", shell=True)
            subprocess.run("systemctl restart BUAgent", shell=True)
           
    '''LAST Backup ran into an ERROR'''
else:
    print("# HELP terra_backup_check Checks if the last Terra Backup was successful ")
    print("# TYPE terra_backup_check gauge")
    print("terra_backup_check 2")
    if restart:
        try:
            subprocess.run("systemctl restart vvagent", shell=True)
            subprocess.run("ps faux | grep -i BUAgent | grep -v color | awk '{ print $2 }' | xargs kill -9", shell=True)
            subprocess.run("systemctl restart vvagent", shell=True)
        except subprocess.SubprocessError:
            subprocess.run("systemctl restart BUAgent", shell=True)
            subprocess.run("ps faux | grep -i BUAgent | grep -v color | awk '{ print $2 }' | xargs kill -9", shell=True)
            subprocess.run("systemctl restart BUAgent", shell=True)
            

print("# HELP terra_backup_check_time Time between Jobs")
print("# TYPE terra_backup_check_time gauge")
print("terra_backup_check_time %s" % (hours_between_jobs))
print("# HELP terra_backup_check_jobage Maximal Jobage")
print("# TYPE terra_backup_check_jobage gauge")
print("terra_backup_check_jobage %s" % (args.max_age))
