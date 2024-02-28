#!/usr/bin/env python3
# This Script was written by Bosse Klein

# --collector.textfile.directory=/var/lib/prometheus/textfile_collector/consul_service_check.prom

import json
import dns.resolver
import dns

file = '/var/lib/prometheus/textfile_collector/consul_service_check.prom'

'''get node name from /etc/consul.d/service.json'''


with open('/etc/consul.d/services.json') as jsonfile:
    jsondata = json.load(jsonfile)
    service_num = len(jsondata['services'])
with open('/etc/consul.d/config.json') as jsonfile2:
    jsondata2 = json.load(jsonfile2)
    datacenter = (jsondata2['datacenter'])

'''Service NUM = Anzahl laufender Services auf der Node'''


def service_exploration(number):
    i = 1 - number

    while 1 > i:
        try:
            name = []
            tags = []
            name = jsondata['services'][i]['name']
            tags = jsondata['services'][i]['tags']
            service_hostname = "{}.{}.service.{}.consul".format(name, tags[0], datacenter)
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2
            resolver.lifetime = 5
            service_ips = []
            resolved_ip = dns.resolver.resolve(service_hostname, 'A')
            for IPval in resolved_ip:
                service_ips.append(IPval.to_text())

            if i == 0:
                return 0

        except dns.exception.Timeout:
            return 1

        except dns.resolver.NXDOMAIN:
            try:
                name = []
                name = jsondata['services'][i]['name']
                service_hostname = "{}.service.{}.consul".format(name, datacenter)
                resolver = dns.resolver.Resolver()
                resolver.timeout = 2
                resolver.lifetime = 5
                service_ips = []
                resolved_ip = dns.resolver.resolve(service_hostname, 'A')
                for IPval in resolved_ip:
                    service_ips.append(IPval.to_text())

                if i == 0:
                    return 0

            except dns.resolver.NXDOMAIN:
                try:
                    service_hostname = "{}.service.consul".format(name)
                    resolver = dns.resolver.Resolver()
                    resolver.timeout = 2
                    resolver.lifetime = 5
                    service_ips = []
                    resolved_ip = dns.resolver.resolve(service_hostname, 'A')
                    for IPval in resolved_ip:
                        service_ips.append(IPval.to_text())
                    if i == 0:
                        return 0

                except dns.resolver.NXDOMAIN:
                    return 2
            i += 1


''' Print Metrics'''


if service_exploration(service_num) not in [1, 2]:
    '''Everything is as it should be'''
    print("# HELP consul_service_check Checks if the .service.consul Address gives an IP-Address back ")
    print("# TYPE consul_service_check gauge")
    print("consul_service_check 0")

elif service_exploration(service_num) == 1:
    '''Server did not answer in Time'''
    print("# HELP consul_service_check Checks if the .service.consul Address gives an IP-Address back ")
    print("# TYPE consul_service_check gauge")
    print("consul_service_check 1")

elif service_exploration(service_num) == 2:
    '''DNS-Servers cannot Resolve the Hostname'''
    print("# HELP consul_service_check Checks if the .service.consul Address gives an IP-Address back ")
    print("# TYPE consul_service_check gauge")
    print("consul_service_check 2")
