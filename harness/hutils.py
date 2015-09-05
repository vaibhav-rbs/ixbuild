import subprocess
import os
import sys
import logging

import report

logger = logging.getLogger(__name__)

logreport = logging.getLogger('report')
logerror = logging.getLogger('report.Reporter.logerror')

def make_common_url(name):
    '''
    Used to create URL string
    for using in API calls
    '''

    common_url = "http://%s/api/v1.0/" % name
    return common_url

def make_url(server, api):
    '''
    Returns whole url for server and api name
    '''
    url = "http://%s/api/v1.0/%s/" % (server, api)
    return url


def make_auth(user, passw):
    '''
    TODO:  
    '''
    auth = (user,passw)
    return auth


def headers():
    headers = {'Content-Type':'application/json'}	
    return headers


def sh_system(command):
    '''
    TODO: use subprocess
    '''
    res = os.system(command)
    if not res == 0:
        logging.error("Command %s failed with code %s" % (command, res))
    return False


def sh(command, halt=False):
    '''
    if halt is True, 
    raise exception 
    for immediate exit
    otherwise return the error message

    TODO: proper logging, etc
    '''
    try:
        child = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    
        out, err = child.communicate()
        logerror = logging.getLogger('errorlogger')
        logerror.setLevel(logging.INFO)
        
        if err and halt == True:
            
            logerror.error(err)
            raise Exception('ERROR: ' + str(err))
    except subprocess.CalledProcessError, data:
        
        traceback.print_exc()
        if halt:
            
            raise ( data + os.linesep + str(err)  )  
    else:
        return err, out


def report(log, info):
    '''
    Old not used
    '''
    with open(log, 'a+') as f:
        writeline(info)	


def printlist(lst):
    '''
    Pretty print
    '''
    for l in lst:
        print l


def nmblookup(hostname):
     '''
     useful utility to get ip address
     for example, does not work...
     '''   

     command = 'nmblookup ' + hostname



