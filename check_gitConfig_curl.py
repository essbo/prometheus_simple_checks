#!/bin/env/python3
# -*- coding: utf-8 -*-

import argparse as arg
import prometheus_client as prom
import subprocess as sub
import pycurl

# initialize variables
host = sub.check_output("/usr/bin/hostname",
                        shell=True).decode("utf-8").strip()

acceptedReturnCodes = [301, 302, 303, 403, 404]

# initialize argparse
args = arg.ArgumentParser(description="Checks if a website is reachable")
args.add_argument("-H",
                  "--hostname",
                  help="The url to check",
                  type=str,
                  )
args = args.parse_args()

# initialize prometheus
registry = prom.CollectorRegistry()
http_check = prom.Gauge('http_check',
                        'Checks if http is reachable 0=OK, 1=TIMEOUT, 2=ERROR',
                        ['hostname', 'http_code'])


# initialize curl
curl = pycurl.Curl()


def doCheck():
    curl.setopt(curl.URL, args.hostname)
    curl.setopt(curl.CONNECTTIMEOUT, 5)
    curl.setopt(curl.TIMEOUT, 5)
    curl.setopt(curl.FOLLOWLOCATION, 1)
    curl.setopt(curl.MAXREDIRS, 5)
    curl.setopt(curl.NOBODY, 1)
    curl.setopt(curl.HEADER, 1)
    curl.setopt(curl.SSL_VERIFYPEER, 0)
    curl.setopt(curl.SSL_VERIFYHOST, 0)
    curl.setopt(curl.FAILONERROR, 1)
    curl.setopt(curl.USERAGENT, "curl/7.52.1")
    curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    curl.perform()
    try:
        responsecode = curl.getinfo(curl.RESPONSE_CODE)
    except pycurl.error:
        responsecode = 999
    return responsecode


def checkStatus():
    registry.register(http_check)
    check = doCheck()
    if check in acceptedReturnCodes:
        http_check.labels(host, check).set(2)
    elif check == 999:
        http_check.labels(host, check).set(1)
    else:
        http_check.labels(host, check).set(0)


checkStatus()
print(prom.generate_latest(registry).decode("utf-8"))
