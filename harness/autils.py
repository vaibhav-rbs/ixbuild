import json
import requests
import commands

import api_list as call
import hutils


def isServiceSet(hostname, serviceName, user, password):

    url = hutils.make_url(hostname, 'services/services')
    auth = hutils.make_auth(user, password)
    result, servicelist = call.get(url, auth)
    for service in servicelist:
        if service['srv_service'] == serviceName:
            #print service['srv_service']
            #print service['srv_enable']
            if service['srv_enable'] == True:
                return True
            
    return False    


def userExists(server, username, passw):
    '''
    Checks by username
    '''
    auth = hutils.make_auth(username, passw)
    url = hutils.make_url(self.host, 'account/users')
    res, text = call.get(url, auth)
    for user in text:
        if user['bsdusr_username'] == username:
            return True
    
    return False  


def volumeExists(server, username, auth, volume):
    '''
    looks for the volume with the name
    '''
    url = hutils.make_url(server, 'storage/volume')  
    res, text = call.get(url, auth)
    auth = hutils.make_auth(username, auth)
    for vol in text:
        if vol['name'] == volume:
            return True

    return False            


def datasetExists(host, user, auth, volumename, datasetname):

    url = hutils.make_url(host, 'storage/volume/' + volumename + '/datasets')
    res, text = call.get(url, (user,auth))
    for dset in text:
        if dset['name'] == datasetname:
            return True

    return False        


def cifsShareExists(host, user, auth, sharename):
    url = hutils.make_url(host, 'sharing/cifs')
    res, text = call.get(url, (user,auth))
    for dset in text:
        if dset['cifs_name'] == sharename:
            return True

    return False          

###########################

def reboot(hostname, user, passwd):
    '''
    reboot the system 
    '''

    print "***********************************"
    print "**** Rebooting " + hostname
    print "***********************************"
    logging.info(" **** Rebooting " + hostname)
    auth = hutils.make_auth(user, passwd)
    url = 'http://' + hostname + '/api/v1.0/system/reboot/'
    if isUp(): 
        r = requests.post(url, auth = auth, headers = headers)
    # wait until system is up
    while not isUp():
        time.sleep(10)
    if not r.status_code == 202:
        return True
         
    return False 


def isUp(hostname ):
    '''
    Check if it is possible to ping the server
    '''
    command = makeSSH('ping -c 2 ' + hostname)
    unreacheable = 'Destination Host Unreachable'
    result = commands.getstatusoutput(command)

    for line in result[1]:
        if line.count(unreacheable):
            logging.info(line)
            return False
    if result[0] == 0:
        return True
    return False                 




