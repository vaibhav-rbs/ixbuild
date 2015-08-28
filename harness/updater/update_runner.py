import os
import sys
import logging
import smtplib 
import traceback
import optparse
import utils
import json
import filecmp
from email.mime.text import MIMEText



import update_software
import api_list as call
import apiUtils


'''



TODO:
further verification of HA servers
should be done from here

check how sheduled tasks ran

Add test for Bug #9718




'''

__doc__ = """
This module is running updater from update_software.py
and afterwards doing some smoke testing

At the end it sends email with a short report as body

"""

__version__ = '1.0'
__usage__ = '''python %prog'''


parser = optparse.OptionParser(usage = __usage__, version = '%prog 1.0')



def sendMail(textfile):
    '''
    Send the report file 
    to recipients
    '''

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.
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
    

def parseAlert(server, msg = 'CRIT'):
    '''
    Just verify there is no any
    bad alert
    '''
    url = utils.make_url(server, 'system/alert')
    status, data = call.get(url)
    if not status == 200:
	raise Exception(url + ' call failed')    
        return False
    for m in data:
        if m.has_key('level'):
	    if m['level'] in ["ERROR", 'CRIT']:
		print m['level'] 
		logging.error('From alert system of server ' + server + str(m['message']))
                return False
    return True


class ServerBase(object):
    '''
    Base class
    for different tests to held
    server information
    '''
    pass



class Server(ServerBase):
    '''
    All the information and utilities
    to setup and get status of the server.
    Some tests that has to compare the state 
    of the server before and after, 
    can also be part of this class, 
    
    '''
    def __init__(self, name, auth = 'abcd1234'):
        self.name = name
        self.update_available = False
        self.updated = False
        self.versionBefore = None
        self.versionAfter = None
               
        self.pair = None
        self.active = None        
        self.v_url = utils.make_url(self.name, 'system/version')
        self.versionBefore = call.get(self.v_url)[1]
        

	# get some information about the server
        self.system = utils.isHA(self.name)

        # for now, keep the results here
	self.results = {'check' : False, 'update' : False, 'reboot': False, 'active_before' : False, 'active_after' : False,  }



    
    def printSelf(self):
	print ' **** State of server ' + self.name
	apiUtils.prettyPrintJson(self.results)
	    
    
    def toString(self):
        s = json.loads(self.results)
        return s


    def testVersions(self):
        '''
        Compare versions before and after the update.
	Since this is internal to the Bunch class,
	and we know that it is updating moslty nightlies,
	for now just make sure last number in the full
	version is larger.
	TODO: more stability
	'''
	result = True
        r, version_after = call.get(self.v_url)
	if not r == 200:
	    result = False
	logging.info(' * Version before update ' + str(self.versionBefore))
        logging.info(' * Version after update ' + str(version_after))
	print type(self.versionBefore)
	print version_after
	if not self.versionBefore['fullversion'].split('-')[3] <= version_after['fullversion'].split('-')[3]:
            result = False
	    logging.error(' **** Comparing versions before and after update/reboot failed')
        
	return result


class Bunch(object):
    '''
    Holds information about HA system. 
    Main reason for it is to 
    manage logs, and being able to compare the state
    of HA before and after some operation,
    for now update

    '''

    def __init__(self, names, train, logpath):
        '''
        This class keeps two lists
	of single servers, and HA pairs
	'''
	self.pairs = []
	self.singles = []
	
	for s in names:
	    if isinstance(s, list):
		bunch = []    
	        for s1 in s:
		    i = Server(s1)
		    bunch.append(i)
		self.pairs.append(bunch)    
	    else:
	   
		i = Server(s)    
		self.singles.append(i)    
		    
	self.train = train
        
	# for comparing results before and after update
	# this directory will have subdirectories for each 
	# server
	self.logpath = logpath
	self.log_before = os.path.join(os.getcwd(), 'log_before')
	self.log_after = os.path.join(os.getcwd(), 'log_after')
	self.report = os.path.join(os.path.split(logpath)[0], 'report.txt')
        
	# each file in directory had unique name: serverName_api_call.json
	# freshly generate directories
	if not os.path.exists(self.log_before):
            os.mkdir(self.log_before)
        if not os.path.exists(self.log_after):
            os.mkdir(self.log_after)	
    
   
    def writeToLog(self, line):
        '''
        For now, the pretty log
	TODO: change to logging module

	'''
        with open(self.report, 'a+') as log:
	    log.write(line)	


        
    def run(self):
	'''
        updating of HA pair 
	and single servers from
	whole list is launched from
	this function
	'''
	res1 = True
	res2 = True
	for s in self.pairs:
	    res1 = self.runPair(s)
	for s in self.singles:
	    res2 = self.runSingle(s)    
	if False in [res1, res2]:
	    return False	


    def runSingle(self, s):
            '''
            Run update software and 
	    reboot for a server
	    that is not a part of HA
	    '''
	
	    result = True
	    server = s.name
            s.printSelf()
            updater = update_software.TestUpdate(server, self.train, log = self.logpath)
            update_available = updater.checkForUpdates()
            s.results['check'] = update_available
            self.writeToLog( " *** Server " + server)
            if update_available:
	        		
	        logging.info(' **** Update available on: ' + server)    
		r =  False
		if r:  # just a debug capability. remove later
		    print ' **** Install updates on: ' + server
		    r = updater.update()
                    
		    line = "Updating server " + server + str(r) 
                    logging.debug(line)
		    self.writeToLog(line)
                    s.results['update'] = r
	    
		    r = updater.reboot()
		    line = "Rebooting server " + server + str(r)
		    logging.info(line)
		    self.writeToLog(line)
                    s.results['reboot'] = r
		    s.updated = r 
                
            return result 

    
    def runPair(self, servers):
	'''
	Run update server and reboot
	for both nodes of HA system
	'''
	result = True
        # for now this is just a pair, but later it can be more than two servers
        for s in servers:
            server = s.name
	    # get version before the update
            # will use to compare to the version after the update
	    active = utils.isActive(server)
            if active:
	        # test before
		s.results['active_before'] = True
		# run the set of the api-s on the active node for HA
		output_location = os.path.join(self.log_before, server)
	        res = getStateByApi(s.name, output_location)
		s.results['api_test'] = res

            # debug
	    #s.printSelf()

            # call update script
            updater = update_software.TestUpdate(server, self.train, log = self.logpath)
	    update_available = updater.checkForUpdates()
	    s.results['check'] = update_available

            if update_available:
	        	
	        logging.info(' **** Update available, install on: ' + server)    
		r =  True
		if r:  # just a debug capability. remove later
		    print ' **** Install updates on: ' + server
	            r = updater.update()
		
                    line = "Updating server " + server + str(r)
		    logging.debug(line)
		    self.writeToLog(line)
                    s.results['update'] = r
	    
		    r = updater.reboot()
		    
		    line = "Rebooting server " + server + str(r)
		    logging.debug(line)
		    self.writeToLog(line)
                    s.results['reboot'] = r
                    s.updated = r 
                    

		res = utils.isActive(server)
	        s.results['active_after'] = res
		if res:
		    output_location = os.path.join(self.log_after, server)
                    res = getStateByApi(s.name, output_location)
                    self.writeToLog(" **** Server state returned by some api-s resulted in " + str(res))

		res = testVersionMismatch(server)    
               	s.results['version_mismatch_test'] = res
		if not res:
                    result = False			

	        
            else:
                line = '**** No update available for: ' + server
		logging.debug(line)
		self.writeToLog(line)
	    s.printSelf()	
		
        
        for pair in self.pairs:
            for s in pair:
	        if s.results['active_before'] == s.results['active_after'] and s.updated == True:
		    line = 'ERROR: Server ' + s.name + ', being part of HA has same state after reboot, this is not an expected behavior'
		    logging.error(line)
		    self.writeToLog(line)
		    result = False 
                else:
			line = ' **** Server ' + s.name + ' is part of HA ' + ' it has been rebooted and changed its state, which is an expected behavior.'  

	return result

    def runTests(self):
        '''
        Run different set of tests on
	pairs and singles
	'''
	result = True
        paired = {}
	single = {}
        for p in self.pairs:
	    sres = dict()	
	    res = failoverTest2(p[0].name, p[1].name)
  
        
	for s in self.singles:
	    res = parseAlert(s.name)	
            res = s.testVersions()

        return result

###############################################
		
def testVersionMismatch(server):
    '''
    Alert system should notify about version mismatch
    #9860   Add alert to warn about access denied and version mismatch in HA
    '''
    
    result = True
    if not utils.isHA(server):
	logging.error(server + " is not part of HA, this test is not applicable")    
        return False
    version_mismatch = ''	
    if not parseAlert(server, msg = version_mismatch):
        result = False
	
    return result

	    
def getStateByApi(server, logdir):
    '''
    Get the state of the server
    running get() api on active node.
    report results
    '''
    result = True
    name = server
    logging.info( '****************************')
    logging.info( ' **** Run some basic api to get info on server: ' + name)
    logging.info( '****************************')
    if not os.path.exists(logdir):
        os.mkdir(logdir)	    
    log_status = os.path.join(os.getcwd(), logdir, 'state.txt')
    urls = ['account/users', 'account/groups', 'network/globalconfiguration', 'network/interface', 'services/services', 'network/interface', 'storage/volume', 'services/iscsi/portal', 'services/iscsi/target',  'services/iscsi/authorizedinitiator', 'services/iscsi/extent',   'services/iscsi/authcredential', 'services/iscsi/targettoextent', 'storage/volume',]
    for u in urls:
        url = utils.make_url(name, u)
	log_out =  os.path.join(os.getcwd(), logdir, u.replace('/', '_') + '.json') 
	result, text = call.get(url, log_out = log_out, log_status = log_status)
        if not result == 200:
	    logging.error('Call to get() for ' + url + ' failed')
            result = False
    return result


def camcontrolTest(server):
    '''
    Dont know yet what is this
    '''
    #camcontrol devlist -v
    return False


def iscsiSetup(server, logdir):
    '''
    Create iscsi target, extent, etc
    TODO: decide what it should return
    '''
    # get first
    logging.info(" **** Setting an iscsi target on " + server)
    purl = utils.make_url(server, 'services/iscsi/portal')
    p = call.get(purl)[1]
    
    turl = utils.make_url(server, 'services/iscsi/target')
    t = call.get(turl)[1]


    iurl = utils.make_url(server, 'services/iscsi/authorizedinitiator')
    i = call.get(iurl)[1]

    eurl =  utils.make_url(server, 'services/iscsi/extent')
    e = call.get(eurl)[1]

    aurl =  utils.make_url(server, 'services/iscsi/authcredential')
    a = call.get(aurl)[1]

    teurl =  utils.make_url(server, 'services/iscsi/targettoextent')
    te = call.get(teurl)[1]

    # create an iscsi block
    pdata = {"iscsi_target_portal_comment": "test2", 
        "iscsi_target_portal_discoveryauthgroup": '', 
        "iscsi_target_portal_discoveryauthmethod": "auto", 
        "iscsi_target_portal_ips": [
            "0.0.0.0:3260"
        ], 
        "iscsi_target_portal_tag": 1
      }
    # step 1, portal
    p_id = call.getId(purl, 'test2')
    
    if p_id:
        res = call.delete(purl + '/' + str(p_id)) 

    p2 = call.post(purl, dataset = pdata)
    
    # step 2 initiator
   
    idata = {
        
        "iscsi_target_initiator_auth_network": "ALL", 
        "iscsi_target_initiator_comment": "test2", 
        "iscsi_target_initiator_initiators": "ALL", 
        }
     
    i_id = call.getId(iurl, 'test2')
    print 'Initiator id is ' + str( i_id)
    if i_id:
        res = call.delete(iurl + '/' + str(i_id))
    p3 = call.post(iurl, dataset = idata)

    # step3 add target
    tdata =  {
          "iscsi_target_name": "test2",
          "iscsi_target_alias": "test2",
          "iscsi_target_mode": "iscsi",
    }
    
    t_id = call.getId(turl, 'test2')
    if t_id:
       res = call.delete(turl + '/' + str(t_id))
    p4 = call.post(turl, dataset = tdata)
 	    
   
    # step4  add device extent
    edata = {
        "iscsi_target_extent_comment": "For testing, will be removed later", 
        "iscsi_target_extent_name": "test2", 
        "iscsi_target_extent_path": "/dev/zvol/tank/test22", 
         }
     
    e_id = call.getId(eurl, 'test2')
    
    if e_id:
        res = call.delete(eurl + '/' + str(e_id))
    p3 = call.post(eurl, dataset = edata)


    # step5  add target/to/extent


    etdata = {
          "test2": 1,
          "test2_extent": 1,
          "iscsi_lunid": "null",
    }


    # step 5 cleanup
     


def powerConsumption(server, logdir):
    '''
    from the bug#9994
    ipmitool dcmi power reading
    '''
    return False


def failoverByReboot(server1, server2, log):
    '''
    - check system status
    - reboot
    - check system status
    - passive should become active, and vice versa
    '''
    logging.info(" **** Test failover by simply rebooting both nodes")
    result = True
    init = {server1: False, server2: False}
    for s in init:
        if utils.isActive(s):
            init[s] = True
    if not False in init.values():
        raise Exception('Two active nodes in a HA setup, something is wrong!!!')
    # reboot both and do the same excersise, and finally compare with the data from "init"	
 	    

    return result


def main():
    '''
    Main entry point for the 
    script to update the servers from the list. 
    Runs some basic tests 
    '''
    result = True
    try:	

        parser.add_option(
  	    '--check',  
	    action='store_true',
	    default = False,
	    help='Check for updates and exit, default:   %default')

	parser.add_option(
	    '--reboot',  
	    action='store_true', 
	    default = False,
	    help = 'Reboot the system(s), default:  %default')
        parser.add_option(
	    '--server',  
	    type = "string",
	    default = '',
	    help='Name of the server to be updated, if empty, update all from the list. Default: %default')

        parser.add_option(
	    '--train',  
	    
	    type = 'choice',
	    choices = ['TrueNAS-9.3-STABLE', 'TrueNAS-9.3-Nightlies'],
	    help='Train name, default: %default', 
	    default = 'TrueNAS-9.3-Nightlies')
        parser.add_option(
	    '--level',  
	    type = 'choice',
	    choices = [logging.DEBUG, logging.INFO],
            help='Level of logging: %default', 
	    default = logging.INFO)


	parser.add_option(
	    '--test',  
	    action = 'store_true',
	    default = False)
        

        args, rest = parser.parse_args()	
        
        print "****    Following options are specified " + str(args)

        
        # define the top level log, create if fresh
        logfile = os.path.join(os.getcwd(), 'logs', 'update_runner.log') 
        if os.path.exists(logfile):
            os.remove(logfile)	
	if not os.path.isdir(os.path.split(logfile)[0]):
	    os.mkdir(os.path.split(logfile)[0])
	  
        log = logging.basicConfig(filename = logfile, level = args.level )
   	    
        b = Bunch([['z20ref-b.sjlab1.ixsystems.com', 'z20ref-a.sjlab1.ixsystems.com'], ], args.train, logfile)
        
	# For now, testing only
        if args.test == True:
	    #res = tests(b.active, os.path.split(logfile)[0])	
	    #iscsiTest('z20ref-b.sjlab1.ixsystems.com', logfile)
            b.runTests()
	    sys.exit(0)

        res = b.run()
        print  " **** Run complete, log is " + b.report + ' and ' + logfile
        sendMail(b.report)
	if res == True:
            sys.exit(0)
    except Exception, data:
	traceback.print_exc()
	print data
	logging.error(data)
	sys.exit(-1)




def testsOld(server):
    '''
    Run some small tests
    '''
    
    res1 = parseAlert(server)
    

def failoverTest2(server1, server2):
    '''
    Tests the failover status
    '''
    result = True
    url1 = utils.make_url(server1, 'failover/failover')

    res1, text1 = call.get(url1, server1)
    url2 = utils.make_url(server2, 'failover/failover')
    res2, text2 = call.get(url2, server2)
    for s, t in zip(text1, text2):
        if not s == t:
	    print s, t
	    result = False
	    logging.info("failoverTest2 failed")
    return result


def volumeStates(server, logdir):
    '''
    checks the states of volumes on server
    '''
    url = utils.make_url('storage/volume')
    res1 = call.get(url, server)
    for child in res1[1]:
        print child['children']       	    


def compareDirs(before, after ):
    '''
    Compares the state before and after the 
    update of the system
    TODO : make it to work 
    indepandently of this module
    in that case can quickly check 
    '''
    result = True
    
    c = filecmp.dircmp(before, after)
    s = c.report()
    logging.info(' **** Comparison of directories ' + before + ' and ' + after)
    logging.info(s)
    return result
	


if __name__ == '__main__':
    main()	
