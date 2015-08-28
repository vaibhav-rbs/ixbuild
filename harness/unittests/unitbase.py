import json
import os
import requests
import logging
import unittest
import sys

import hutils

#TODO: logging, parse args

logger = logging.getLogger(__name__)
fh = logging.FileHandler('out.log', mode='w')
logger.addHandler(fh)

class TestBase(unittest.TestCase):

    
    def setUp(self):

        #self.parseArgs()
        self.host = '10.5.0.171'
        self.user = 'root'
        self.password = 'abcd1234'
        self.auth = hutils.make_auth(self.user, self.password)

        self.logdir = os.path.join(os.getcwd(), 'output')
        self.golddir = os.path.join(os.getcwd(), 'ref')
        
           
        
               

    