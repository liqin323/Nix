#!/usr/local/bin/python2.7

import sys
from optparse import OptionParser
import os
import httplib
import json
from base64 import b64encode
import requests

__author__ = 'liqin'


def main():
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage, version='%prog 1.0')

    parser.add_option('--ip', dest='ip', help='app server ip address')
    parser.add_option('--applicant', dest='applicant', help='applicant')
    parser.add_option('--tenant', dest='tenantID', help='tenant ID')
    parser.add_option('--product', dest='productID', help='product ID')
    parser.add_option('--key', dest='key', help='API key')
    parser.add_option('--token', dest='token', help='access token')
    parser.add_option('--name', dest='name', help='server name')
    parser.add_option('--type', dest='type', help='server type')

    options, args = parser.parse_args()
    if not (options.tenantID and options.productID and options.key and options.token and options.name and options.type):
        parser.print_help()
        return 1

    try:
        api_key = b64encode(options.key).decode('ascii')
        req_headers = {'Content-type': 'application/json;charset=UTF-8', 'Authorization': 'Basic %s' % api_key}

        req_data = {'name': options.name, 'type': options.type, 'applicant': options.applicant,
                    'tenant_id': options.tenantID, 'product_id': options.productID}
        req_body = json.dumps(req_data)

        post_url = 'https://%s/v2/servers?accessToken=%s' % (options.ip, options.token)
        resp = requests.post(post_url, headers=req_headers, verify=False, data=req_body)

        resp.status_code

        if resp.status_code == httplib.CREATED:
            respJson = resp.json()

            id = respJson['href'].split('/')[-1]
            get_url = 'https://%s/v2/servers/%s?accessToken=%s' % (options.ip, id, options.token)

            resp = requests.get(get_url, headers=req_headers, verify=False)
            svr_info = resp.json()
            print svr_info

            try:
                key_file = os.path.join(os.path.abspath('.'), svr_info['name'])

                with open(key_file, mode='w') as f:
                    f.write(svr_info['key'])
            except Exception as e:
                parser.error('%s' % e)

    except Exception as e:
        parser.error('Error: %s' % e)

    return


if __name__ == '__main__':
    sys.exit(main())
