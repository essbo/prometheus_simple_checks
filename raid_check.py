#!/usr/bin/env python3
'''This Script was written by Bosse Klein

Settings to add to the Node_Exporter.service
--collector.textfile.directory=/var/lib/prometheus/textfile_collector/raid_check.prom'''

import subprocess as sus

'''Get Values'''
raid = sus.getoutput("/opt/MegaRAID/storcli/storcli64 /c0 /vall show | egrep -c \"State | Optl\"")
'''Get Values'''

'''Print Output depending on the Values'''
if raid == "2":
    print("# HELP raid_check Checks if the Raid-Drive is in the Opt. State ")
    print("# TYPE raid_check gauge")
    print("raid_check 0")
else:
    print("# HELP raid_check Checks if the Raid-Drive is in the Opt. State ")
    print("# TYPE raid_check gauge")
    print("raid_check 1")
