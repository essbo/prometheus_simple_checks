#!/bin/env/python3
# -*- coding: utf-8 -*-
# Author:
#  - Bosse Klein

# This script connects to a remote host and checks if the given website is
# reachable
# and checks for certain response codes
# The script is meant to be used in a cronjob

import pickle as rick
import base64 as b64
import os
import sys
import argparse as arg
import requests as req
import asyncio as aio
import asyncssh as ssh
import prometheus_client as prom
import re
import logging as log

# from imports
from logging.handlers import TimedRotatingFileHandler as rfh
from systemd.journal import JournalHandler as jh

# define variables
local_test = 0


def list_of_strings(arg):
    return arg.split(',')


parser = arg.ArgumentParser(description="checks via remote-host http-codes")

parser.add_argument("-r",
                    "--remote",
                    help="The remote host",
                    default="localhost")

parser.add_argument("-p",
                    "--port",
                    help="The remote port",
                    default=22)

parser.add_argument("-u",
                    "--user",
                    help="The remote user",
                    default="root")

parser.add_argument("-i",
                    "--identity",
                    help="The identity file",
                    default=None)

parser.add_argument("-pw",
                    "--password",
                    help="The remote password",
                    default=None)

parser.add_argument("-s",
                    "--secret",
                    help="Path to the secret file",
                    type=str)

parser.add_argument("--codes",
                    help="The http codes to check for",
                    type=list_of_strings)

parser.add_argument("--targethost",
                    help="The http host",
                    default="localhost")

parser.add_argument("-l",
                    "--logging",
                    help="Enable logging",
                    action="store_true")

parser.add_argument("-ll",
                    "--loglevel",
                    help="Set loglevel",
                    default="INFO")

# create prometheus registry
registry = prom.CollectorRegistry()

# create prometheus metrics
http_remote_check = prom.Gauge('http_remote_check',
                               'Checks if http is reachable',
                               ['targethost',
                                'remote',
                                'port',
                                'user'
                                ])

http_local_check = prom.Gauge('http_local_check',
                              'Checks if http is reachable',
                              ['targethost'])

http_Remote_check_status = prom.Gauge('http_remote_check_status',
                                      'Checks if the check is working')

args = parser.parse_args()

if args.logging is True:
    """
    Creates a rotating log
    """
    log.basicConfig(level=args.loglevel,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='/var/log/http_remote_check.log',)
    # define a Handler which writes INFO messages or higher to the sys.stderr
    logger = log.getLogger("RedmineExporter")
    logger.setLevel(args.loglevel)

    # add a rotating handler
    handler = rfh("/var/log/http_remote_check.log",
                  when="d",
                  interval=1,
                  backupCount=5)

    journalhandler = jh()
    logger.root.addHandler(journalhandler)
    logger.root.addHandler(handler)
    logger.info('Logging enabled')
    logger.info('Journal logging enabled')

if args.secret:
    try:
        with (open(args.secret, "rb")) as secret_input:
            secret = rick.load(secret_input)
            secret = eval(b64.b64decode(secret))
            secret = dict(secret)
            args.remote = secret["remote"]
            args.port = secret["port"]
            args.user = secret["user"]
            args.codes = secret["codes"]
            args.targethost = secret["targethost"]

            while True:
                if args.identity is None and args.password is None and args.remote == "localhost":
                    local_test = 1

                if secret["password"] is not None:
                    args.password = secret["password"]
                    args.identity = None
                    local_test = 0

                if secret["identity"] is not None:
                    args.identity = secret["identity"]
                    args.password = None
                    local_test = 0
                break

    except Exception as e:
        logger.critical("CRITICAL: Could not load secret file: {}".format(e))

if args.identity is not None and local_test == 0:
    if not os.path.isfile(args.identity):
        logger.critical("CRITICAL: Identity file not found")
        sys.exit(2)

if args.password is None and args.identity is None and local_test == 0:
    logger.critical("CRITICAL: No password or identity file given")
    sys.exit(2)

if args.codes is None and local_test == 0:
    logger.critical("CRITICAL: No http codes given")
    sys.exit(2)

if local_test == 1:
    logger.debug("DEBUG: Entering local mode")


async def run_client(host,
                     command: str) -> None:
    if args.identity is not None:
        async with ssh.connect(host=host,
                               username=args.user,
                               client_keys=args.identity,
                               port=args.port,
                               known_hosts=None) as conn:

            return await conn.run(command)

    if args.password is not None:
        async with ssh.connect(host=host,
                               username=args.user,
                               password=args.password,
                               port=args.port,
                               known_hosts=None) as conn:

            return await conn.run(command)


async def ssh_http_remote_check() -> None:
    command = "curl -I -L {}".format(args.targethost)
    task = (run_client(args.remote,
                       command))

    http_remote_check_results = await aio.gather(task,
                                                 return_exceptions=True)

    for result_http_remote in enumerate(http_remote_check_results):
        if result_http_remote is not None:
            http_Remote_check_status.set(1)
        result = list(result_http_remote)
        match = re.search(r'HTTP/1\.1 (\d+)', result[1].stdout)
        if match:
            http_status_code_remote = int(match.group(1))
            http_remote_check.labels(args.targethost,
                                     args.remote,
                                     args.port,
                                     args.user).set(http_status_code_remote)


def local_http_check():
    try:
        target = "http://{}".format(args.targethost)
        response = req.get(target)
        http_status_code_local = response.status_code
        http_local_check.labels(args.targethost).set(http_status_code_local)
    except Exception as e:
        logger.critical("CRITICAL: {}".format(e))


# main-entrypoint
if __name__ == "__main__":
    try:
        registry.register(http_Remote_check_status)
        registry.register(http_remote_check)
        registry.register(http_local_check)
        aio.new_event_loop().run_until_complete(ssh_http_remote_check())
        local_http_check()
        print(prom.generate_latest(registry).decode("utf-8"))
    except Exception as e:
        logger.critical("CRITICAL: {}".format(e))
        sys.exit(2)
    else:
        sys.exit(0)
