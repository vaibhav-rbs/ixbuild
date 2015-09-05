import json
import os
import requests
import logging
import unittest
import sys

import hutils

#TODO: logging, parse args

#logger = logging.getLogger(__name__)
#fh = logging.FileHandler('out.log', mode='w')
#logger.addHandler(fh)

class TestBase(unittest.TestCase):

    
    def setUp(self):
        '''
        initialization
        '''

        filename = sys.modules[self.__module__].__file__
        testdir = os.path.realpath(filename)
        testdir = os.path.split(testdir)[0]
        self.name = os.path.splitext(os.path.basename(filename))[0]
        self.logdir = os.path.join(testdir, 'output')
        self.golddir = os.path.join(os.getcwd(), 'ref')
        create_dir(self.logdir)

        self.logpath = os.path.join(self.logdir, self.name +'.out')
        
        self.host = '10.5.0.171'
        self.user = 'root'
        self.password = 'abcd1234'
        self.auth = hutils.make_auth(self.user, self.password)
           
        #clsname = type(self.__name__)
        clsname = str(self.__class__)
        
        setup_logger(self.name, self.logpath) 
        self.log = logging.getLogger(self.name)
        self.log.info('Starting tests in module: ' + self.name)
        
    def tearDown(self):
        self.footer()
           

    def custom_assert(self, f1, f2):
        '''

        '''
        if f1 == f2:
            self.log.error('File ' + f1 + ' and '  + ' differ')
        
               

    def custom_diff(self):
        '''
        For comparing goldens with logs
        '''
        pass


    def header(self):
        '''
        informative header
        '''
        self.log.info('Starting time')
        


    def footer(self):
        self.log.info('\n***********************\n')
        #self.log.info(dir(self))


def setup_logger(logger_name, log_file, level=logging.INFO):
    '''
    TODO: move to hutils
    '''
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


def create_dir(dirpath):
    '''
    maybe an overkill now
    but later may be useful
    to avoid race condition 
    in case tests run 
    simultaneously
    '''
    import errno
    if not os.path.isdir(dirpath):
        try:
            os.makedirs(dirpath)
        except OSError as exception:
            if exception.errono != errno.EEXIST:
                raise
