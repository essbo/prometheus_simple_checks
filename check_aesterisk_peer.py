#!/bin/env/python3
# -*- coding: utf-8 -*-

import argparse as arg
import prometheus_client as prom
import asyncssh as ssh
import asyncio as aio
import pickle as rick
import base64 as b64
import re


# initialize variables
result_dict = {}
result_dict2 = {}
result_List = []
commands = []

# initialize custom Argument


def list_of_strings(arg):
    return arg.split(',')


# initialize argparse
args = arg.ArgumentParser(description="Checks aesterisk peer connection")

args.add_argument("-H",
                  "--host",
                  help="The host to check",
                  type=str,
                  required=True)

args.add_argument("-p",
                  "--port",
                  help="The ssh-port",
                  type=int,
                  default=22)

args.add_argument("-u",
                  "--user",
                  help="The ssh-user",
                  type=str,
                  default="root")

args.add_argument("-P",
                  "--password",
                  help="The ssh-password",
                  type=str,
                  default=None)

args.add_argument("-k",
                  "--key",
                  help="The ssh-key",
                  type=str,
                  default=None)

args.add_argument("-s",
                  "--secret",
                  help="The secret file",
                  type=str,
                  default=None)

args.add_argument("--peers",
                  help="A set of peers to check - Comma seperated",
                  type=list_of_strings,
                  default=None)

args = args.parse_args()

# read secrets
if args.secret:
    with (open(args.secret, "rb")) as secret_input:
        secret = rick.load(secret_input)
        secret = eval(b64.b64decode(secret))
        secret = dict(secret)
        args.server = secret["host"]
        args.port = secret["port"]
        args.user = secret["user"]
        args.password = secret["password"]
        args.key = secret["key"]
        args.peers = secret["peer"]

# initialize prometheus metrics
registry = prom.CollectorRegistry()
aesterisk_peer_check = prom.Gauge('aesterisk_peer_check',
                                  'Checks aesterisk peers',
                                  ['host', 'peer'])


async def run_client(host, port, user, command: str) -> None:
    if args.key:
        async with ssh.connect(host=host,
                               port=port,
                               username=user,
                               client_keys=args.key,
                               known_hosts=None) as conn:
            return await conn.run(command)
    if args.password:
        async with ssh.connect(host=host,
                               port=port,
                               username=user,
                               password=args.password,
                               known_hosts=None) as conn:
            return await conn.run(command)


async def ssh_peer_check() -> None:

    for peer in args.peers:
        template_command = "cat /etc/asterisk/peer_status.txt | grep "
        commands.append(template_command + "'" + peer + "'")

    for command in commands:
        task = (run_client(args.host,
                           args.port,
                           args.user,
                           command))

        peer_results = await aio.gather(task,
                                        return_exceptions=True)

        for result_peer in enumerate(peer_results):
            result = (result_peer[1].stdout.strip(" "))
            result = " ".join(result.split())
            result = list(re.split(r'\s', result))
            if result[5] == "OK":
                result_dict[command] = 0
            else:
                result_dict[command] = 1
    return result_dict

try:
    registry.register(aesterisk_peer_check)
    result_dict = aio.run(ssh_peer_check())
    for v in result_dict:
        peer = list(re.split(r'\s', v))
        peer = peer[4]
        aesterisk_peer_check.labels(args.host, peer).set(result_dict[v])
except Exception as e:
    aesterisk_peer_check.labels(args.host, "NULL").set(2)

# print the prometheus metrics
print(prom.generate_latest(aesterisk_peer_check).decode("utf-8"))
