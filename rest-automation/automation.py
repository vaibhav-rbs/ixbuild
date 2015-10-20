import json
import requests
import argparse
import sys

class Startup(object):
    def __init__(self, hostname, user, secret):
        self._hostname = hostname
        self._user = user
        self._secret = secret
        self._ep = 'http://%s/api/v1.0' % hostname
    def request(self, resource, method='GET', data=None):
        x='%s/%s/' % (self._ep, resource)
        data=json.dumps(data)
        headers={'Content-Type': "application/json"}
        auth=(self._user, self._secret)
        response=requests.request(method,x,data=data,headers=headers,auth=auth)
        return response

    def _get_disks(self):
        disks = self.request('storage/disk')
        return [ disk.get('disk_name') for disk in disks.json()]

    def _get_volumes(self):
        volumes = self.request('storage/volume')
        return volumes.json()

    def delete_volume(self):
        volumes = self._get_volumes()
        for volume in volumes:
            volume_id = volume.get('id')
            self.request('storage/volume', method='DELETE', data={
                'destroy': 'true',
                'cascade':'true'
            })

    def create_volume(self):
        disks = self._get_disks()
        response = self.request('storage/volume', method='POST', data={
            'volume_name': 'vb-tank',
            'layout': [
                {'vdevtype': 'stripe', 'disks': disks},
            ],
        })

    def create_pool(self):
        disks = self._get_disks()
        self.request('storage/volume', method='POST', data={
            'volume_name': 'tank',
            'layout': [
                    {
                        'vdevtype': 'stripe',
                        'disks': disks
                     },
            ],
        })

    def create_dataset(self):
        self.request('storage/volume/tank/datasets', method='POST', data={
            'name': 'vb-cifs-auto-cifs-ds',
        })

    def create_cifs_share(self):
        self.request('sharing/cifs', method='POST', data={
            'cifs_name': 'vb-cifs-auto-cifs-share',
            'cifs_path': '/mnt/tank/vb-cifs-auto-cifs-ds',
            'cifs_guestonly': True
        })

    def service_start(self, name):
        self.request('services/services/%s' % name, method='PUT', data={
            'srv_enable': True,

        })

if __name__ == '__main__':
    login = Startup('qa-fn93-nightlies.sjlab1.ixsystems.com/','root','abcd1234')
    login.create_volume()
