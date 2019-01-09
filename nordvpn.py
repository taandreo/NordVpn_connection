#!/usr/bin/python3
import sys
import urllib.request
import json
import re
from time import sleep
import subprocess
import threading

def usage():
    print('''Usage:\n
                -u: Update the repository from nordvpn api.
                -c <Country Code>: Find the best server for the informed country.''', file=sys.stderr)
    sys.exit(1)

def fatal(msg):
    print("Error:\n\t%s" %msg, file=sys.stderr)
    sys.exit(1)

def Update():
    try:
        json_data = (urllib.request.urlopen('https://api.nordvpn.com/server').read()).decode("utf-8")
    except urllib.error.URLError:
        fatal('Connection with nordvpn api failed.')
     
    json_file = open("servers.json", "w")
    json_file.write(json_data)
    json_file.close()

def ping_parsing(ping):
    suum = 0
    raw_ms = re.findall(r'time=[0-9]\.?[0-9]\.?[0-9]', ping)
    
    if len(raw_ms) != 4:
        return -1
    for ms in raw_ms:
        suum += float(ms.replace('time=', ''))
    
    return suum/4
        

def ms_test(server, lock):
    global ms_list

    ping = subprocess.Popen(["ping", "-c", "4", server[1]], stdout=subprocess.PIPE).communicate()[0]
    ping = ping.decode("utf-8")
        
    i = 0
    while(i < 3):
        ms = ping_parsing(ping)
        if ms != -1:
            lock.acquire()
            ms_list.append((server[0], ms))
            lock.release()
            return 0
        i += 1

def LowerFloat(lista):
    m = lista[0]

    for e in lista:
        if e[1] < m[1]:
            m = e
    return m


def Connection():
    if len(sys.argv) < 3:
        usage()
    try:   
        json_file = open('servers.json', 'r')
    
    except FileNotFoundError:
        fatal('Server list not found\n\tRun "nordvpn -u" for update the server list.')
     
    json_data = json_file.read()
    json_file.close()
    
    server_list = json.loads(json_data)
    
    country_servers = []
    
    i = 0

    for server in server_list:
        if server['flag'] == sys.argv[2].upper():
            country_servers.append((i, server['ip_address']))
        i += 1 # Index
    if not country_servers:
        fatal('Bad Argument: "%s"\n\t"%s" is a country code ?' %(sys.argv[2], sys.argv[2])) 
    
    global ms_list
    ms_list = []

    jobs = []
    lock = threading.Lock()

    for server in country_servers:
        p = threading.Thread(target=ms_test, args=(server, lock))
        p.start()
        jobs.append(p)
    
    for p in jobs:
        p.join()
    
    BestServer = LowerFloat(ms_list)
    
    dic = server_list[BestServer[0]]
    
    print('Name: %s' %(dic['name']))
    print('IP Address: %s' %(dic['ip_address']))
    print('Domain: %s' %(dic['domain']))
    print('MS: %.2f' %(BestServer[1]))
    print('Country: %s' %(dic['country']))

def main():
    if len(sys.argv) < 2:
        usage()
    
    elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
        usage()
    
    elif sys.argv[1] == '-u':
        Update()
    
    elif sys.argv[1] == '-c':
        Connection()
    
    else:
        fatal('Bad Argument: %s' %sys.argv[1])

if __name__ == '__main__':
    main()
