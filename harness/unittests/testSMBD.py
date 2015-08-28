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


logger = logging.getLogger(__name__)




class TestSMBD(unitbase.TestBase):
    

    logger = logging.getLogger()

    def setUp(self):
        
        super(TestSnmp, self).setUp()
        
        self.setSNMPService()

    def setSMBService(self):
        if not autils.isServiceSet(self.host, 'cifs', self.user, self.password):
            
            payload =   {
                              
                              "cifs_srv_max_protocol": "SMB2",
                              "snmp_community": "public",
                              "snmp_traps": "false",
                              "snmp_contact": "",
                              "snmp_location": "",
                              "id": 1
                        }
            url = hutils.make_url(self.host, 'services/cifs')
            
            res, text = call.post(url, self.auth, dataset = payload)
            
        

    def test_smb_1(self):
        
        #command = 'snmpwalk -v 2c -c public -t ' + self.host + 'FREENAS-MIB:zfsFilesystemAvailableKB'
        #err, out = hutils.sh(command, halt = True)
        
        command = "sbclient //10.5.0.171/tomsshare -U 'VM-IP171\tomford'"
       
        

        if err:
          logging.error(err)
        logging.info(out)  

    def test_snmp_2(self):
        pass

if __name__ == '__main__':

    # TODO: make a central class and proper command line parsing
    # for now, call it like
    # python testSNMP.py 'root' 'abcd1234' '10.5.0.171'
    if len(sys.argv) > 1:
        TestSnmp.host = sys.argv.pop()
        TestSnmp.password = sys.argv.pop()
        TestSnmp.user = sys.argv.pop()
    unittest.main(verbosity=3)


