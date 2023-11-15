#!/bin/env/python3

import argparse as arg
import subprocess as sub
import prometheus_client as prom
import os

hostname = sub.check_output("/usr/bin/hostname",
                            shell=True).decode("utf-8").strip()

# Parse arguments
args = arg.ArgumentParser(description="Checks Amount of Files in a Directory")
args.add_argument("-d",
                  "--directory",
                  help="The directory to check",
                  type=str)

args.add_argument("-w",
                  "--warning",
                  help="The warning threshold",
                  default=5000)

args.add_argument("-c",
                  "--critical",
                  help="The critical threshold",
                  default=10000)

args = args.parse_args()

# Initialize prometheus metrics
registry = prom.CollectorRegistry()

file_count = prom.Gauge('file_count',
                        'Current File Count',
                        ['directory', 'host'])

file_count_warning = prom.Gauge('file_count_warning',
                                'Warning Threshold 1 if surpassed',
                                ['directory', 'host'])

file_count_critical = prom.Gauge('file_count_critical',
                                 'Critical Threshold 1 if surpassed',
                                 ['directory', 'host'])

# Register prometheus metrics
registry.register(file_count)
registry.register(file_count_warning)
registry.register(file_count_critical)


while True:
    counted_files = 0
    for path in os.listdir(args.directory):
        if os.path.isfile(os.path.join(args.directory, path)):
            counted_files += 1
    if counted_files > int(args.critical):
        file_count_critical.labels(args.directory, hostname).set(1)
    else:
        file_count_critical.labels(args.directory, hostname).set(0)

        if counted_files > int(args.warning):
            file_count_warning.labels(args.directory, hostname).set(1)
        else:
            file_count_warning.labels(args.directory, hostname).set(0)

    file_count.labels(args.directory, hostname).set(counted_files)
    break
# Print the prometheus metrics
print(prom.generate_latest(registry).decode("utf-8"))
