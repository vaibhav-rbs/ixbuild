import sys
import os
import optparse
import unittest
import json
import requests
import logging

import hutils
import autils
import api_list as call
import unitbase



class TestVolume(unitbase.TestBase):

    logger = logging.getLogger()

    def setUp(self):
        self.user = 'testuser'
        self.sharename = 'testshare'
        self.userpass = self.password         # just for symplicity
        super(TestVolume, self).setUp()
        self.createVolume()

    '''

    def setCIFSService(self):
        if not autils.isServiceSet(self.host, 'cifs', self.user, self.password):
            print "CIFS NOT SET"
            payload =   { "cifs_srv_hostlookup": false  }
            url = hutils.make_url(self.host, 'services/snmp')
            
            res, text = call.post(url, self.auth, dataset = payload)
            
    
    def createUser(self):
        found  = False 
        payload = {
          "bsdusr_username": "myuser",
          "bsdusr_creategroup": True,
          "bsdusr_full_name": self.user,
          "bsdusr_password": self.userpass,
          
        }
        url = hutils.make_url(self.host, 'account/users')
        res, text = call.get(url, self.auth)
        for user in text:
            if user['bsdusr_username'] == 'myuser':
                found = True
        if not found:        
            res, text = call.post(url, self.auth, dataset = payload)
        
    '''

    def createVolume(self):
        payload = {
           "volume_name": "tank",
           "layout": [
            {
                   "vdevtype": "stripe",
                   "disks": ["ada1", "ada2"]
            }
                  ]
        }
        found = False
        url = hutils.make_url(self.host, 'storage/volume')  
        res, text = call.get(url, self.auth)
        for vol in text:
            if vol['vol_name'] == 'tank':
                found = True
        if not found:   
            res, text = call.post(url, self.auth, dataset)
        url = hutils.make_url(self.host, 'storage/volume/tank/datasets')
        res, text = call.get(url, self.auth)
        for dset in text:
            if dset['name'] == 'cifsshare':
                found = True
        if not found:
            res, text = call.post(self.host, url, dataset)
         

    def createShare(self):
        url = hutils.make_url(self.host, 'sharing/cifs')
        res, text = call.get(url, self.auth)
        print text

    def test_Import_volume_1(self):

        #  

        # TODO: first import volume


        # now run commands to check conditions

        command1 = 'zpool status tank'
        # TODO: parse this command 
        command = 'sqlite3 /data/freenas-v1.db "select * from storage_disk;"'
        print command
        err, out = hutils.sh(command, halt = True)
        
        if err:
          logging.error(err)
        logging.info(out)  

    def test_Volume_Encryption_2(self):

        '''
        Tests behavrio or BUG #10571
        '''
        command1 = 'sqlite3 /data/freenas-v1.db "select * from storage_encrypteddisk;"'
        command2 = 'sqlite3 /data/freenas-v1.db "select * from storage_volume;"'

        


if __name__ == '__main__':

    # TODO: make a central class and proper command line parsing
    # for now, call it like
    # python testSNMP.py 'root' 'abcd1234' '10.5.0.171'
    if len(sys.argv) > 1:
        TestCIFS.host = sys.argv.pop()
        TestCIFS.password = sys.argv.pop()
        TestCIFS.user = sys.argv.pop()
    unittest.main()
