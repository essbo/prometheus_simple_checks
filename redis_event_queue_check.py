#!/bin/env/python3
# -*- coding: utf-8 -*-

# A check that will check the redis event queue and print prometheus-metriks
# with the current queue size
# This is useful for monitoring the redis event queue
# It will export to a .prom file that can be read by prometheus-node-exporter
# depending on the thresholds it will also print a critical or warning message


import argparse
import redis
import sys
import prometheus_client as prom
import pickle as rick
import re


def list_of_strings(arg):
    return arg.split(',')


# Parse arguments
parser = argparse.ArgumentParser(description="Checks redis queue size")

parser.add_argument("-H",
                    "--host",
                    help="The redis host",
                    default="localhost")

parser.add_argument("-p",
                    "--port",
                    help="The redis port",
                    default=6379)

parser.add_argument("-P",
                    "--password",
                    help="The redis password",
                    default=None)

parser.add_argument("-q",
                    "--queue",
                    help="The redis queues seperated by ,",
                    type=list_of_strings)

parser.add_argument("-w",
                    "--warning",
                    help="The warning threshold",
                    default=5000)

parser.add_argument("-c",
                    "--critical",
                    help="The critical threshold",
                    default=10000)

parser.add_argument("-s",
                    "--secret",
                    help="Path to the secret file",
                    type=str)

args = parser.parse_args()

if args.secret:
    try:
        with (open(args.secret, "rb")) as secret_input:
            secret = rick.load(secret_input)
            args.password = secret["password"]
            args.host = secret["host"]
            args.port = secret["port"]
            args.queue = secret["queue"]

    except Exception as e:
        print("CRITICAL: Could not load secret file: {}".format(e))
        sys.exit(2)
# initialize variables
qeue = {}

# Initialize prometheus metrics

registry = prom.CollectorRegistry()

redis_queue_size = prom.Gauge("redis_queue_size",
                              "The size of the redis queue",
                              ["queue"])

redis_queue_critical = prom.Gauge("redis_queue_critical",
                                  "The Critical threshold has been surpassed",
                                  ["queue"])

redis_queue_warning = prom.Gauge("redis_queue_warning",
                                 "The Warning threshold has been surpassed",
                                 ["queue"])

registry.register(redis_queue_size)
registry.register(redis_queue_critical)
registry.register(redis_queue_warning)

# Connect to redis
try:
    redis = redis.Redis(host=args.host,
                        port=args.port,
                        password=args.password)
except Exception as e:
    print("CRITICAL: Could not connect to redis: {}".format(e))
    sys.exit(2)

# Print the metric
if args.queue is None:
    keys = redis.keys('*')
    for key in keys:
        key_type = redis.type(key)
        if key_type == b'list':
            try:
                queue_size = redis.llen(key)
            except Exception as e:
                print("CRITICAL: Could not get queue size: {}".format(e))
                sys.exit(2)
            redis_queue_size.labels(key).set(queue_size)
            if queue_size > args.critical:
                redis_queue_critical.labels(key).set(1)
            else:
                redis_queue_critical.labels(key).set(0)
            if queue_size > args.warning:
                redis_queue_warning.labels(key).set(1)
            else:
                redis_queue_warning.labels(key).set(0)
else:
    for queue in args.queue:
        try:
            queue_size = redis.llen(queue)
        except Exception as e:
            print("CRITICAL: Could not get queue size: {}".format(e))
            sys.exit(2)
        redis_queue_size.labels(queue).set(queue_size)
        if queue_size > args.critical:
            redis_queue_critical.labels(queue).set(1)
        else:
            redis_queue_critical.labels(queue).set(0)
        if queue_size > args.warning:
            redis_queue_warning.labels(queue).set(1)
        else:
            redis_queue_warning.labels(queue).set(0)


# Print the prometheus metrics
print(prom.generate_latest(registry).decode("utf-8"))
