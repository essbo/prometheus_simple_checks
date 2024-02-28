#!/usr/bin/python3

'This Script was written by Bosse Klein'

import subprocess
import argparse

arg = argparse.ArgumentParser()
arg.add_argument("-r", "--response", required=False, help="If set the script will check the response time of the sql-instance ", action='store_true')
arg.add_argument("-p", "--process", required=False, help="If set the script will check if the mariadb process is running", action='store_true')
arg.add_argument("-c", "--cluster", required=False, help="If set the script will check if the mariadb process is running", action='store_true')
args = arg.parse_args()

if args.response:
    response = 1
else:
    response = 0

if args.process:
    process = 1
else:
    process = 0

if args.cluster:
    cluster = 1
else:
    cluster = 0


def response_check():
    response = subprocess.check_output(["mysql", "-e", "SELECT SLEEP(1);"])
    if "1" in str(response):
        return 1
    else:
        return 0


def determine_cluster():
    response = subprocess.check_output(["mysql", "-e", "SHOW STATUS LIKE 'wsrep_connected';"])
    if "ON" in str(response):
        return 1
    else:
        return 0


def process_check():
    process = subprocess.check_output(["ps", "-ef"])
    if "mysqld" in str(process):
        return 1
    else:
        return 0


def galera_cluster_check():
    clustersize = subprocess.check_output(["mysql", "-e", "SHOW STATUS LIKE 'wsrep_cluster_size';"])
    if "3" in str(clustersize):
        return 1
    else:
        return 0


if cluster == 1:
    try:
        print("# HELP galera_cluster_running Determines if a galera cluster is running")
        print("# TYPE galera_cluster_running gauge")
        if determine_cluster() == 1:
            print("galera_cluster_running 1")
            print("# HELP galera_cluster_check Checks if the galera cluster has the right amount of machines inside the cluster")
            print("# TYPE galera_cluster_check gauge")
            if galera_cluster_check() == 1:
                print("galera_cluster_check 1")
            else:
                print("galera_cluster_check 0")
        else:
            print("galera_cluster_running 0")
    except subprocess.CalledProcessError:
        print("galera_cluster_running 0")


if process == 1:
    try:
        print("# HELP mysql_process_check Checks if the mysql process is running ")
        print("# TYPE mysql_process_check gauge")

        if process_check() == 1:
            print("mysql_process_check 1")
        else:
            print("mysql_process_check 0")
    except subprocess.CalledProcessError:
        print("mysql_process_check 0")

if response == 1:
    try:        
        print("# HELP mysql_response_check Checks if the mysql server is responsive")
        print("# TYPE mysql_response_check gauge")

        if response_check() == 1:
            print("mysql_response_check 1")
        else:
            print("mysql_response_check 0")
    except subprocess.CalledProcessError:
        print("mysql_response_check 0")
