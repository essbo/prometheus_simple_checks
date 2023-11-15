#!/bin/env/python3
# -*- coding: utf-8 -*-

# A check that will check the ldap server and print prometheus-metrics
# if it is reachable
# This is useful for monitoring the ldap connection
# It will export to a .prom file that can be read by prometheus-node-exporter
# if needed you can also check the ldap connection via ssh
# This may be used to connect to Securepoint UTMs and check the LDAP Connection

import argparse
import ldap3
import prometheus_client as prom
import asyncssh as ssh
import asyncio
import pickle as rick
import base64


# initialize variables
result_dict = {}
result_List = []

# initialize custom Argument


def list_of_strings(arg):
    return arg.split(',')


# parse arguments
parser = argparse.ArgumentParser(description="Checks ldap connection")
parser.add_argument("-S",
                    "--server",
                    help="The ldap server",
                    default="localhost")

parser.add_argument("-p",
                    "--port",
                    help="The ldap port",
                    default=389)

parser.add_argument("-b",
                    "--base",
                    help="The ldap base - LDAP SYNTAX ONLY")

parser.add_argument("-u",
                    "--user",
                    help="The ldap user",
                    default="cn=admin")

parser.add_argument("-P",
                    "--password",
                    help="The ldap password")

parser.add_argument("--ssh",
                    help="Connect via ssh and do the tests",
                    default=False,
                    action="store_true")

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

parser.add_argument("-s", "--secret",
                    help="The secrets-file",
                    type=str)

args = parser.parse_args()

# read secrets
if args.secret:
    with (open(args.secret, "rb")) as secret_input:
        secret = rick.load(secret_input)
        secret = eval(base64.b64decode(secret))
        secret = dict(secret)
        args.server = secret["server"]
        args.port = secret["port"]
        args.base = secret["base"]
        args.user = secret["user"]
        args.password = secret["password"]
        args.sshuser = secret["sshuser"]
        args.sshpassword = secret["sshpassword"]
        args.sshhosts = secret["sshhosts"]
        args.sshport = secret["sshport"]
        args.key = secret["key"]


# initialize prometheus metrics
registry = prom.CollectorRegistry()
ldap_check = prom.Gauge('ldap_check',
                        'Checks if ldap is reachable',
                        ['server'])

ldap_check2 = prom.Gauge('ldap_check2',
                         'Checks if ldap is reachable via ssh',
                         ['server', 'host'])


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


async def ssh_ldap_check() -> None:
    for host in args.sshhosts:
        command = "spauthcli lsgroupsremote | grep white"

        task = (run_client(host,
                           command))

        ldap_results = await asyncio.gather(task,
                                            return_exceptions=True)

        for result_ldap in enumerate(ldap_results):
            result = list(result_ldap)
            if result[1].stderr == "" and result[1].stdout != "":
                result_dict[host] = 1
            elif result[1].returncode != 0:
                result_dict[host] = 0
            else:
                result_dict[host] = 0

if args.ssh is False:
    try:
        registry.register(ldap_check)
        server = ldap3.Server(args.server,
                              port=args.port,
                              get_info=ldap3.ALL)

        conn = ldap3.Connection(server,
                                args.user,
                                args.password,
                                auto_bind=True)

        conn.search(args.base,
                    '(memberOf=*)')

        ldap_check.labels(args.server).set(1)

    except Exception:
        ldap_check.labels(args.server).set(0)


if args.ssh is True:
    registry.register(ldap_check2)
    asyncio.new_event_loop().run_until_complete(ssh_ldap_check())

    for host, state in result_dict.items():
        ldap_check2.labels(args.server, host).set(state)

print(prom.generate_latest(registry).decode("utf-8"))
