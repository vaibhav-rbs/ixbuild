import os
import sys
import json
import logging

import build
import hutils
import hdescr 

class Test:
    def __init__(self, info):
        self.info = info              


class Tester(object):
    '''
    
    Tester class handles running
    the test suites that are set
    to run in harness

    '''
    def __init__(self, config):
       '''
       Keeps track on all
       input information
       '''
       try:
          
           self.config = config 
           self.__result = True             # will be set to False once anything fails 
           self.report = '' 
           self.testlist = hdescr.tests.keys() 
	   #self.servers = self.testlist['servers']
	   print self.testlist
       except Exception, data:
           print data
           raise     

    @property
    def result(self):
        return self.__result	    
       
    def sanityCheck(self):
	'''
	Make sure all the
	necessary software/hardware 
	is in place,
	remove tests that do not 
	have proper setup
	'''
        pass	    


    def toString(self):
	'''
        Formats the results of the run
	'''
        for t in self.tests:
            self.report = self.report + str(t) + ':\t' + str('Pass')
        return self.report

    def runTests(self):
        pass        	    
    
            	    
class VBoxBasic(object):
    '''
    Creates Virtual Box and 
    installs from given image 
    '''
    def __init__(self, isodir, platform='freeBsd64', name = 'newVM'):
        '''
        installs a vm and 
        does silent installation
        '''
        self.isofile = None
        for f in os.listdir(isodir):
            if f.endswith('iso'):	
	        self.isofile = f
	

    def setup(self):
        self.installVM()



    def installVM(self):
	'''
	install vbox
	'''
        res = sh('./2.runtests.sh')	  
	if not res:
	    # TODO: do not forget to get real output and print into exception	
            raise Exception('Installing Virtual Box failed')	


def main():
    '''
    Just for testing purposes
    '''  

    newvm = VBoxBasic()
    


