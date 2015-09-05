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


class TestSnmp(unitbase.TestBase):
    
    def setUp(self):
        super(TestSnmp, self).setUp()
        self.snmp = self.getsnmp()
        self.setSNMPService()

    def setSNMPService(self):
        payload =   {
                              "snmp_options": "",
                              "snmp_community": "public",
                              "snmp_traps": "false",
                              "snmp_contact": "",
                              "snmp_location": "",
                              "id": 1
                    }
         # this activates the service           
        if not autils.isServiceSet(self.host, 'snmp', self.user, self.password):
            autils.setService(self.host, 'snmp', self.user, self.password)             
        # now set the way we need it
        url = hutils.make_url(self.host, 'services/services/snmp/')
            
        res, text = call.put(url, self.auth, dataset = payload)
            
        
    def getsnmp(self):
        if os.uname()[0] == 'FreeBSD':
            return 'bsnmpwalk'
        if os.uname()[0] == 'Linux':
            return 'snmpwalk'       


    @unittest.skipIf(os.uname()[0] == 'FreeBSD',
                     "snmp utility not on FreeBSD")
    def test_snmp_1(self):
        
        command = self.snmp + ' -v 2c -C public -t ' + self.host + ' FREENAS-MIB:zfsFilesystemAvailableKB'
        print command
        err, out = hutils.sh(command, halt = True)
        
        if err:
          logging.error(err)
        logging.info(out)  

    def test_snmp_2(self):
        pass


if __name__ == '__main__':

    # TODO: make a central class and proper command line parsing
    # for now, call it like
    # python testSNMP.py 'root' 'abcd1234' '10.5.0.171'
    '''
    if len(sys.argv) > 1:
        TestSnmp.host = sys.argv.pop()
        TestSnmp.password = sys.argv.pop()
        TestSnmp.user = sys.argv.pop()
    '''
        
    unittest.main()


