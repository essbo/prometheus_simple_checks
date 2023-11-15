#!/bin/env/python3
# -*- coding: utf-8 -*-

import dns
import dns.resolver
import argparse as arg
import prometheus_client as prom


# intialize variables
dns_output = {}


# initialize argparse
args = arg.ArgumentParser(description="Checks dns resolution")
args.add_argument("-H",
                  "--hostname",
                  help="The hostname to check",
                  type=str,
                  required=True)

args.add_argument("-a",
                  "--address",
                  help="The address to check",
                  type=str)

args.add_argument("-s",
                  "--server",
                  help="The server to check",
                  type=str,
                  default="8.8.8.8")

args.add_argument("--tcp",
                  help="Use tcp instead of udp",
                  action="store_true")

args.add_argument("-r",
                  "--record",
                  help="The record to check",
                  type=str,
                  default="A")


# parse arguements
args = args.parse_args()

# initialize prometheus
registry = prom.CollectorRegistry()
dns_check = prom.Gauge('dns_check',
                       'Checks if dns is reachable 0=OK, 1=TIMEOUT, 2=ERROR',
                       ['hostname', 'address',
                        'server', 'port', 'record'])

# initialize dns resolver
resolver = dns.resolver.Resolver()
resolver.timeout = 5
resolver.lifetime = 5

if args.server:
    resolver.nameservers = [args.server]

# register prometheus metrics
registry.register(dns_check)

try:

    if args.tcp:
        dns_output1 = dns.resolver.query(args.hostname, args.record, tcp=True)
    else:
        dns_output1 = dns.resolver.query(args.hostname, args.record)

    print(dns_output1)
    dns_check.labels(args.hostname,
                     args.address,
                     args.server,
                     args.tcp,
                     args.record).set(0)

except dns.exception.DNSException as e:
    if e == dns.exception.Timeout:
        dns_check.labels(args.hostname,
                         args.address,
                         args.server,
                         args.tcp,
                         args.record).set(1)
    else:
        dns_check.labels(args.hostname,
                         args.address,
                         args.server,
                         args.tcp,
                         args.timeout,
                         args.record).set(2)

# print the prometheus metrics
print(prom.generate_latest(registry).decode("utf-8"))
