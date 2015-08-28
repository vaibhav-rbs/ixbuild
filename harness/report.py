import os
import sys
import json
import time
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


__doc__ = """

This module can run only when the run
information from harness is available.
It will load the information and generate a
report which can be emailed 

"""

#TODO: logging. all to be generated afresh too

class Node:
    '''
    NOt decided yet
    '''
    def __init__(self):
        self.children = []


# 
class ReporterOld:
    '''
    This is old version, keep until
    decided which logging to use
    ''' 

    def __init__(self, build, test, log):
	    
        self.log = log
        if os.path.exists(log):
            os.remove(log)

        self.log = log 

        self.logfile = open(log, 'a+')
        logging.basicConfig(filename='LoggingReport.log',level=logging.INFO)
	    
        self.buildinfo = build
        self.testinfo = test 
        #print self.buildinfo.report()
        self.header()     

    def __init__(self, log):
      
        self.log = log
        if os.path.exists(log):
            os.remove(log)
            
        self.log = log 

        self.logfile = open(log, 'a+')
        self.header()


    def setBuildInfo(self, buildinfo):
        self.buildinfo = buildinfo

    def setTestInfo(self, testinfo):
        self.testinfo = testinfo


    def header(self):
       localtime = time.localtime()
       self.write('HARNESS RUN RESULTS')
       self.write('Time: ' + time.strftime("%Y:%D:%H:%M:%S"))
                                                     
    def reportBuild(self):
       self.write('Build results: ' )
       self.write(self.buildinfo.report)

    def reportTest(self):
        self.write('Test Results: ')
        self.write(self.testinfo.report)

    def header2(self):
       localtime = time.localtime()	    
       	    
       self.write('HARNESS RUN RESULTS/n')
       self.write('Time: ' + time.strftime("%Y:%D:%H:%M:%S"))
       self.write('Build results: ')
       self.write(self.buildinfo.report)
       self.write('Test Results: ')
       self.write(self.testinfo.report)
       self.logfile.close()  

    
    def write(self, line):
        self.logfile.write(line + '\n')	    


    def emailReport(self):
       '''
       creates an html
       email and sends
       '''

    @property
    def result(self):
        '''
	all results together
	'''
	if False in [self.buildinfo.result, self.testinfo.result]:
            return False
        return True


    def emailReport(self, textfile = None):
        '''
        Send the report file 
        to recipients
        '''

        # Open a plain text file for reading.  For this example, assume that
        # the text file contains only ASCII characters.
	if not textfile:
            textfile = 	self.log	
        fp = open(textfile, 'rb')
        # Create a text/plain message
        msg = MIMEText(fp.read())
        fp.close()

        me = 'lilit@ixsystems.com'
        you = 'lilit@ixsystems.com'
        msg['Subject'] = 'Results of running %s' % textfile
        msg['From'] = me
        msg['To'] = you

        # Send the message via our SMTP server, but don't include the
        # envelope header.
        #s = smtplib.SMTP('localhost')
        s = smtplib.SMTP('10.2.55.1')
        s.sendmail(me, [you], msg.as_string())


errorlogger = logging.getLogger('errorlogger')
reportlogger = logging.getLogger('reportlog')


formatter = logging.Formatter('%(message)s')

eh = logging.FileHandler('error.log')
rh = logging.FileHandler('report.log')

eh.setFormatter(formatter)
rh.setFormatter(formatter)

reportlogger.addHandler(rh)
errorlogger.addHandler(eh)



class Reporter:
    '''
    Manage the main Report.log

    '''
    def __init__(self, logpath):
        '''

        '''
        
        if os.path.exists(logpath):
            os.remove(logpath)
        # later maybe remove recreate whole dir
        logdir = os.path.split(logpath)[0]
        if not os.path.isdir(logdir):
          os.mkdir(logdir)

        eh = logging.FileHandler('error.log')
        rh = logging.FileHandler(logpath)
        self.error_logger = errorlogger
        #self.error_logger.setLevel(logging.ERROR)
        self.error_logger.setLevel(logging.INFO)
        self.header()     
    
    def setBuildInfo(self, buildinfo):
        self.buildinfo = buildinfo

    def setTestInfo(self, testinfo):
        self.testinfo = testinfo


    def header(self):
       localtime = time.localtime()
       
       self.error_logger.info('HARNESS RUN RESULTS')
       self.error_logger.info('Time: ' + time.strftime("%Y:%D:%H:%M:%S"))

    def reportBuild(self):
       self.write('Build results: ' )
       self.write(self.buildinfo.report)

    def reportTest(self):
        self.write('Test Results: ')
        self.write(self.testinfo.report)
