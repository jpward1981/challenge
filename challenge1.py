#!/usr/bin/env python

import argparse
import requests
import json
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help = "Base hostname to user for servers")
    parser.add_argument('-c', '--count', type=int, default=3, help="Nubmer of server to build, default 3")
    parser.add_argument('-f', '--flavor', help="Flavor of server")
    parser.add_argument('-i', '--image' ,  help="Image to build from ")
    parser.add_argument('-r', '--region', help="Region to build server")
    parser.add_argument('-u', '--username', required=1, help="Username")
    parser.add_argument('-k', '--apikey', required=1, help="API Key")

    args = parser.parse_args()

    auth_url = "https://identity.api.rackspacecloud.com/v2.0/tokens"
    auth_data = {
        'auth': {
            'RAX-KSKEY:apiKeyCredentials': {
                'username': args.username,
                'apiKey': args.apikey
            }
        }
    }
    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json'
    }
    r = requests.post(auth_url, data=json.dumps(auth_data), headers=headers)
    auth_response = r.json()
    service_catalog = auth_response['access']['serviceCatalog']
    token = auth_response['access']['token']['id']
    tenant = auth_response['access']['token']['tenant']['id']

    cloud_server_catalog_key = 'cloudServersOpenStack'
    
    headers['X-Auth-Token'] = token

    endpoint = None

    for service in service_catalog:
        if service['name'] == cloud_server_catalog_key:
            for ep in service['endpoints']:
                if ep['region'] == args.region:
                    endpoint = ep['publicURL']
                    break
            break
    if not endpoint:
        raise SystemExit('Endpoint Not Found')

    servers = {}

    for i in xrange(0,args.count):
        name =  '%s%d' % (args.base, i)
        server_data = { 
            'server' : {
                'flavorRef': args.flavor,
                'imageRef': args.image,
                'name' : name
            }
        }
        server_url = '%s/servers' % endpoint
        r = requests.post(server_url, data=json.dumps(server_data), headers=headers)
        servers[name] = r.json()['server']
    
    completed = []
    while len(completed) < args.count: 
        if name in completed: 
            print '%s: 100%%' % name,
            continue
        server_url='%s/servers/%s'  % (endpoint, servers[name]['id'])
        r = requests.get(server_url, headers=headers)
        detail = r.json()['server']
        servers[name] = dict(servers, **detail)
        print '%s: %s%%' % (name, detail['progress']),
        if detail['status'] in ['ACTIVE', 'ERROR']:
            completed.append(name)
            if detail['status'] == 'ERROR':
                requests.delete(server_url, headers=headers)
        print
        time.sleep(30)

    for name,server in servers.iteritems():
        print 'Name: %s' % name
        
if __name__ == '__main__':
    main()
