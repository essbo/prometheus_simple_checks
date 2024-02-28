                                                                                                 
#!/usr/bin/python3

'This Script was written by Bosse Klein'

import argparse
import asyncio
import asyncssh


'''Argparse-Checks'''
arg = argparse.ArgumentParser()
arg.add_argument("-u", "--utm", required=True, help="IP - Address / Hostname of the Master-UTM (Hostnames are Recommended)", nargs="+", type=str)
arg.add_argument("-c", "--check", required=False, help="Checks the Version of the UTM Cluster", action='store_true')
arg.add_argument("-s", "--sync", required=False, help="Checks the sync Status of the UTM Cluster", action='store_true')
arg.add_argument("-v", "--verbose", required=False, help="A verbose output for debugging", action='store_true')
arg.add_argument("-k", "--key", required=True, help="Define the name of the key for authentication", type=str)
args = arg.parse_args()
'''Argparse-Checks'''

'''Set Variables to run the selected checks'''
check = 1 if args.check else 0
get = 1 if args.sync else 0
verbose = 1 if args.verbose else 0
keyfile = args.key

'''Set Variables to run the selected checks'''
'''Set global vars'''

hosts = args.utm

versions = []
status = []
finished_version = {}
finished_sync = {}

'''Async SSHConnection'''


async def run_client(host, command: str) -> asyncssh.SSHCompletedProcess:
    async with asyncssh.connect(host, username='root', client_keys=[keyfile]) as sshconn:
        return await sshconn.run(command)

'''Async SSHConnection'''


'''Run both version-checks simoultaniously'''


async def run_multiple_clients_version() -> None:
    # Put your lists of hosts here
    global versions
    for host in hosts:
        tasks = (run_client(host, 'cat /etc/VERSION'))
        results = await asyncio.gather(tasks, return_exceptions=True)
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                finished_version[host] = "Failed"
                if verbose == 1:
                    print('Task %d failed: %s' % (i, str(result)))
            elif result.exit_status != 0:
                versions.append("SSH-Exception")
                if verbose == 1:
                    print('Task %d exited with status %s:' % (i, result.exit_status))
            else:
                result = result.stdout
                result = result.strip()
                finished_version[host] = result.strip()
                if verbose == 1:
                    print(result.stdout, end='')

'''Run both sync-cheks simoultaniously'''


async def run_multiple_clients_get() -> None:
    # Put your lists of hosts here
    global status
    for host in hosts:
        tasks = (run_client(host, "spcli -j cluster info | jq -r '.result.content[1].value'"))
        results = await asyncio.gather(tasks, return_exceptions=True)
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                finished_sync[host] = "Failed"
                if verbose == 1:
                    print('Task %d failed: %s' % (i, str(result)))
            elif result.exit_status != 0:
                status.append("SSH-Exception")
                if verbose == 1:
                    print('Task %d exited with status %s:' % (i, result.exit_status))
            else:
                result = result.stdout
                finished_sync[host] = result.strip()
                if verbose == 1:
                    print(result.stdout, end='')


'''Print metrics and run ssh commands'''


if check == 1:
    print("# HELP utm_version_check Checks if the master returns a version")
    print("# TYPE utm_version_check gauge")
    asyncio.new_event_loop().run_until_complete(run_multiple_clients_version())
    for key, value in finished_version.items():
        if value == "Failed":
            print("utm_version_check{host=\"" + key + "\", version=\"" + value + "\"} 2")
        elif value == "SSH-Exception":
            print("utm_version_check{host=\"" + key + "\", version=\"" + value + "\"} 1")
        elif value != "SSH-Exception" and value != "Failed":
            print("utm_version_check{host=\"" + key + "\", version=\"" + value + "\"} 0")

if get == 1:
    print("# HELP utm_sync_check Checks if the UTM-Cluster is in sync")
    print("# TYPE utm_sync_check gauge")
    asyncio.new_event_loop().run_until_complete(run_multiple_clients_get())
    for key1, value1 in finished_sync.items():
        if value1 == "synchronized":
            print("utm_sync_check{host=\"" + key1 + "\"} 0")
        elif value1 == "timeout":
            print("utm_sync_check{host=\"" + key1 + "\"} 1")
        elif value1 == "versions differ":
            print("utm_sync_check{host=\"" + key1 + "\"} 2")
        elif value1 == "pending":
            print("utm_sync_check{host=\"" + key1 + "\"} 3")
        elif value1 == "error":
            print("utm_sync_check{host=\"" + key1 + "\"} 4")
        elif value1 == "SSH-Exception":
            print("utm_sync_check{host=\"" + key1 + "\"} 5")
        elif value1 == "Failed":
            print("utm_sync_check{host=\"" + key1 + "\"} 6")
