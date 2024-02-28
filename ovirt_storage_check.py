#!/usr/bin/env python3
# This script was written by Bosse Klein - Securepoint GmbH
# It is an adaption of the oVirt-Storage-Monitroing script written by Marc-Daniell Hess

from bitmath import Byte
import ovirtsdk4
import argparse
import secrets_1
import logging


'''Create a Connection with the Ovirt-Api '''
connection = ovirtsdk4.Connection(url=secrets_1.URL, username=secrets_1.USERNAME, password=secrets_1.PASSWORD, ca_file=secrets_1.CA_FILE,)

'''Define Functions'''


def calcGiB(bytes):
    bytes = Byte(bytes)
    gib = bytes.to_GiB()
    return float(gib)


def calcTotal(available, used):
    total = available + used
    return total


def calcPercentUsed(total, used):
    percent = used / total * 100
    return percent



'''Get StorageDomains from Ovirt'''
storageDomains = []
storageDomains_get = connection.system_service().storage_domains_service()
storageDomains = storageDomains_get.list()

'''Build Argparse'''
arg = argparse.ArgumentParser()
arg.add_argument("-d", "--domain", required=False, help="Define the Storagedomains that are supposed to be looked up - if left empty every domain is going to be checked", nargs="+", type=str)
arg.add_argument("-t", "--threshold", required=True, help="Define the threshold in GIB or percent if you're going to use the -p argument(If I < Threshold - Do nothing, IF I > Threshold - Do something)", type=int)
arg.add_argument("-p", "--percent", required=False, help="Print percentage of the Values instead of GiB  - Default True", action='store_true')
arg.add_argument("-v", "--verbose", required=False, help="Prints more information - Default False", action='store_true')
args = arg.parse_args()

'''Define Variables passed to Argparse'''
domain = args.domain
if args.verbose:
    verbose = 1
    logging.info('Verbose Mode is enabled')
    logging.info('Trying to fetch StorageDomains')
else:
    verbose = 0

threshold = args.threshold
if args.percent:
    percent = 1



'''Add Logging'''
if verbose == 1:
    log = "/var/log/prometheus/oVirt-Storage-Check.log"
    logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')


if domain is None:
    print("# HELP Checks ovirt_storage_check if a storage domain is full or not")
    print("# TYPE ovirt_storage_check gauge")
    for storageDomain in storageDomains:
        if percent == 1:
            if verbose == 1: 
                logging.info('Trying to fetch % Values')
                logging.info("Calculating % Values")
            percent_available = calcGiB(storageDomain.available)
            percent_used = calcGiB(storageDomain.used)
            percent_total = calcTotal(percent_available, percent_used)
            used_percent = round(calcPercentUsed(percent_total, percent_used))
            if verbose == 1: 
                logging.info("Done.")
            if threshold > 100:
                if verbose == 1: 
                    logging.info('This is not working. Are you sure you want to use % ?')
                    logging.info("Switching to GiB Mode.")
                usedGiB = calcGiB(storageDomain.used)
                availableGiB = calcGiB(storageDomain.available)
                totalGib = calcTotal(availableGiB, usedGiB)
                if usedGiB <= threshold:
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
                else:
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 1")
            else:
                if verbose == 1: 
                    logging.info('Using % - Values')
                if used_percent <= threshold:
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
                else:  
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 1")
        else:
            if verbose == 1: 
                logging.info('Trying to fetch GiB Values')
            usedGiB = calcGiB(storageDomain.used)
            availableGiB = calcGiB(storageDomain.available)
            totalGib = calcTotal(availableGiB, usedGiB)
            if verbose == 1: 
                logging.info('Done.')          
            if usedGiB <= threshold:
                print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
            else:
                print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 1")
else:
    print("# HELP ovirt_storage_check Checks if a storage domain is full or not")
    print("# TYPE ovirt_storage_check gauge")
    for storageDomain in storageDomains:
        if storageDomain.name in domain:
            if percent == 1:
                if verbose == 1:
                    logging.info('Trying to fetch % Values')
                    logging.info("Calculating % Values")

                percent_available = calcGiB(storageDomain.available)
                percent_used = calcGiB(storageDomain.used)
                percent_total = calcTotal(percent_available, percent_used)
                used_percent = round(calcPercentUsed(percent_total, percent_used))
                if verbose == 1: 
                    logging.info("Done.")
                if threshold > 100:
                    if verbose == 1: 
                        logging.info('This is not working. Are you sure you want to use % ?')
                        logging.info("Switching to GiB Mode.")
                    usedGiB = calcGiB(storageDomain.used)
                    availableGiB = calcGiB(storageDomain.available)
                    totalGib = calcTotal(availableGiB, usedGiB)
                    if usedGiB <= threshold:
                        print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
                    else:
                        print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 1")
                else:
                    if verbose == 1: 
                        logging.info('Using % - Values')
                    if used_percent <= threshold:
                        print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
                    else:  
                        print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"}1")
            else:
                if verbose == 1: 
                    logging.info('Trying to fetch GiB Values')
                usedGiB = calcGiB(storageDomain.used)
                availableGiB = calcGiB(storageDomain.available)
                totalGib = calcTotal(availableGiB, usedGiB)
                if verbose == 1: 
                    logging.info('Done.')

                if usedGiB <= threshold:
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"} 0")
                else:
                    print("ovirt_storage_check{storageDomain=\"" + str(storageDomain.name) + "\"}1")

if domain is None:
    print("# HELP ovirt_storage_total Total Usage of the Storage Domain")
    print("# TYPE ovirt_storage_total gauge")
    for storageDomain in storageDomains:
        usedGiB = calcGiB(storageDomain.used)
        availableGiB = calcGiB(storageDomain.available)
        totalGib = calcTotal(availableGiB, usedGiB)
        print("ovirt_storage_total{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(totalGib))

    print("# HELP ovirt_storage_used used Usage of the Storage Domain")
    print("# TYPE ovirt_storage_used gauge")
    for storageDomain in storageDomains:
        usedGiB = calcGiB(storageDomain.used)
        print("ovirt_storage_used{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(usedGiB))

    print("# HELP ovirt_storage_available available Usage of the Storage Domain")
    print("# TYPE ovirt_storage_available gauge")
    for storageDomain in storageDomains:
        availableGiB = calcGiB(storageDomain.available)
        print("ovirt_storage_available{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(availableGiB))

else:
    print("# HELP ovirt_storage_total Total Usage of the Storage Domain")
    print("# TYPE ovirt_storage_total gauge")
    for storageDomain in storageDomains:
        if storageDomain.name in domain:
            usedGiB = calcGiB(storageDomain.used)
            availableGiB = calcGiB(storageDomain.available)
            totalGib = calcTotal(availableGiB, usedGiB)
            print("ovirt_storage_total{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(totalGib))

    print("# HELP ovirt_storage_used used Usage of the Storage Domain")
    print("# TYPE ovirt_storage_used gauge")
    for storageDomain in storageDomains:
        if storageDomain.name in domain:
            usedGiB = calcGiB(storageDomain.used)
            print("ovirt_storage_used{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(usedGiB))

    print("# HELP ovirt_storage_available available Usage of the Storage Domain")
    print("# TYPE ovirt_storage_available gauge")
    for storageDomain in storageDomains:
        if storageDomain.name in domain:
            availableGiB = calcGiB(storageDomain.available)
            print("ovirt_storage_available{storageDomain=\"" + str(storageDomain.name) + "\"} " + str(availableGiB))
