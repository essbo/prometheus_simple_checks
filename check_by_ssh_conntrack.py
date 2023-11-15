#!/bin/env/python3
# -*- coding: utf-8 -*-

import argparse
import prometheus_client as prom
import asyncssh as ssh
import asyncio
import pickle as rick
import base64


# initialize variables
result_dict = {}
result_dict2 = {}
result_List = []

# initialize custom Argument


def list_of_strings(arg):
    return arg.split(',')


# parse arguments
parser = argparse.ArgumentParser(description="Checks conntrack via ssh connection")

parser.add_argument("--sshuser",
                    help="The ssh user",
                    default="root")

parser.add_argument("--sshpassword",
                    help="The ssh password",
                    default=None)

parser.add_argument("--sshhosts",
                    help="The ssh host",
                    type=list_of_strings)

parser.add_argument("--sshport",
                    help="The ssh port",
                    default=22)

parser.add_argument("--key",
                    help="The ssh key")

parser.add_argument("--secret",
                    help="The secret file")

args = parser.parse_args()

# read secrets
if args.secret:
    with (open(args.secret, "rb")) as secret_input:
        secret = rick.load(secret_input)
        secret = eval(base64.b64decode(secret))
        secret = dict(secret)
        args.sshuser = secret["sshuser"]
        args.sshpassword = secret["sshpassword"]
        args.sshhosts = secret["sshhosts"]
        args.sshport = secret["sshport"]
        args.key = secret["key"]


# initialize prometheus metrics
registry = prom.CollectorRegistry()
nf_conntrack_max = prom.Gauge('max_connections',
                              'Checks the max connections possible',
                              ['host'])

current_connections = prom.Gauge('current_connections',
                                 'Checks if the current conntack connections',
                                 ['host'])

# connect to ldap server


async def run_client(host,
                     command: str) -> None:
    if args.key:
        async with ssh.connect(host=host,
                               username=args.sshuser,
                               client_keys=args.key,
                               port=args.sshport,
                               known_hosts=None) as conn:

            return await conn.run(command)

    if args.sshpassword is not None:
        async with ssh.connect(host=host,
                               username=args.sshuser,
                               password=args.sshpassword,
                               port=args.sshport,
                               known_hosts=None) as conn:

            return await conn.run(command)


async def ssh_conntrack_check() -> None:
    for host in args.sshhosts:
        command = "cat /proc/sys/net/netfilter/nf_conntrack_max"
        task = (run_client(host,
                           command))
        ssh_results = await asyncio.gather(task,
                                           return_exceptions=True)
        for ssh_conntrack in enumerate(ssh_results):
            result = list(ssh_conntrack)
            if result[1].stderr == "" and result[1].stdout != "":
                result_dict[host] = result[1].stdout
            else:
                result_dict[host] = 0


async def ssh_currentcon_check() -> None:
    for host in args.sshhosts:
        command = "cat /proc/sys/net/netfilter/nf_conntrack_count"
        task = (run_client(host,
                           command))
        ssh_results = await asyncio.gather(task,
                                           return_exceptions=True)
        for ssh_conntrack in enumerate(ssh_results):
            result = list(ssh_conntrack)
            if result[1].stderr == "" and result[1].stdout != "":
                result_dict2[host] = result[1].stdout
            else:
                result_dict2[host] = 0


registry.register(nf_conntrack_max)
registry.register(current_connections)
asyncio.new_event_loop().run_until_complete(ssh_conntrack_check())
asyncio.new_event_loop().run_until_complete(ssh_currentcon_check())
for host, state in result_dict.items():
    nf_conntrack_max.labels(host).set(state)

for host, state in result_dict2.items():
    current_connections.labels(host).set(state)

print(prom.generate_latest(registry).decode("utf-8"))
