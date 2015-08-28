import os
import commands
import optparse
import re
import traceback
import subprocess
import requests
import json
import sys
import time
import logging

import hutils
import api_list as call


__doc__ = """

Utility to upgrade freeNAS and TrueNAS installations
uses freeNAS utility /usr/local/bin/freenas_update
requires keyless SSH login set up to work properly.
TODO: add support with no keyless access

Checks for the installed version on system,
checks for available updates, 
though freenas_update check, 
installs update, reboots.

for calling from another scipt,
create an in stance of TestUpdate
"""


__usage__ = """usage: python %prog [--system <systemname>][--update] [--train] = <TRAIN>] [--check] [--reboot] [--version]  """

parser = optparse.OptionParser(usage = __usage__, version = '%prog 1.0')


class TestUpdate(object):
    '''
    Check if updates are available
    runs update
    reboots
    checks generated update logs
    reports the result
    Verify the update
    check the version before update
    and after update/reboot.
    Version string will be
    updated after the reboot
    
    '''


    def __init__(self, server, train, check = True, download = None, log = '' ):
        '''
        Set options for the
	freenas_update utility
	and other stuff
	'''
        
	self.server = server
	self.check = check
        self.user = 'root' 
        self.trainName = train
        self.train = ' -T ' + train + ' '  		
        
	if not download == None:
            self.download = ' -d '
        else:     
            self.download = ''

        self.update_available = False
        
	# if the log exists, do not recreate it
	if log == '':
	    logpath = os.path.join(os.getcwd(), 'logs', self.server + "_update.log")
            if os.path.exists(logpath):
                os.remove(logpath)		
        else:
	    logpath = log	
	if not os.path.exists(os.path.split(logpath)[0]):
            os.mkdir(os.path.split(logpath)[0])		

        self.log = logging.basicConfig(filename = logpath, level = logging.DEBUG )
        self.logpath = logpath

        # keep this to not call check 
	# more than once during the lifetime
	self.needsUpdate = False
        self.setUp()

         
    def setUp(self):
        '''
	Setup and 
	sanity check

	'''
        self.getServerName()
        if not self.isUp():
            raise Exception( "**** Unknown server specified:  " + self.server)		
        self.versionControl()


    def versionControl(self):
        '''
       	Control safety of the 
	system from not supported upgrades
	'''
        url = hutils.make_url(self.server, 'system/version/')
	r, text = call.get(url)
	if not r == 200:
	    raise Exception('Could not get version of system ' + self.server)
        fullversion = text['fullversion']
	version = text['version']
	current_train = self.trainName.split('-')
        update_train  = fullversion.split('-')
	
	for x, y in zip(current_train, update_train):
	    if not x == y:
	        raise Exception("The OS installed on server " + self.server + ' is ' + fullversion	+ ' while you are trying to upgrade it to ' + self.trainName + '. This is not allowed. Exiting...')

    
    def checkForUpdates(self):
        '''
	Run the command to check for the 
	updates
	parse, then call the update
	For the result of checking be positive
	both shell exit and the logs parsing
	result must be True

	'''
	print "*************************************"
	print "**** Checking for software updates on " + self.server
        print "**************************************\n"

        result = True
        command = self.makeSSH('freenas-update  ' + self.train + ' check')
        output = commands.getstatusoutput(command)
	if not output[0] == 0:
	    result = False	
	if not self.parseCheckOutput(output[1]):	
	    result = False 
            logging.info(" **** No update available for " + self.server)  	
        return result
    
    
    def isUp(self):
        '''
	Check if it is possible to ping the server
	'''
	command = self.makeSSH('ping -c 2 ' + self.server)
	unreacheable = 'Destination Host Unreachable'
        result = commands.getstatusoutput(command)

	for line in result[1]:
            if line.count(unreacheable):
                print line
		return False
	if result[0] == 0:
            return True
        return False


    def runCommand(self, command = ''):
        '''
        TODO: not implemented yet	
	'''
	output  = ''
	if command == '':
	    command = self.makeSSH('ls').split()	
	print 'THIS IS THE COMMAND ' + str(command)    
        p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
       	
        result = p.stdout.readlines()
	print "stdout.readlines() output " + str(result)
	if not result:
	    err = p.stderr.readlines()	
            print err
         
	output = p.communicate()
        print "Output of communicating with server is "  + str(output) 
	if output[1].count('Host key verification failed'):
            print "The system should  be added to the server for passwordless access"
	    sys.exit(-1)
        else:
	    return output

    
    def software_version(self):
	'''
	gets the version through cat /etc/version 
	command on the server. Handy for checking 
	if the upgrade changed it after the reboot

	TODO: get versions also through the api and 
	uname -a output and compare

	'''
        command = self.makeSSH('cat /etc/version')
        output = commands.getstatusoutput(command)
	if output[0] != 0:
            raise Exception("cat /etc/version command failed on remote server")
        version = output[1]
        
        print "\n*************************************************"
	print "****  Version  " + version 
	print "**************************************************"
	return version


    def makeSSH(self, command):
	'''
	helper to make an ssh command
	ready to run
	'''
        command = 'ssh ' + self.user + '@' + self.server + ' "' + command + '"'
	return command


    def getServerName(self, ip = None):
        '''
        helper to run uname -a 
	to find more information about the server
	'''
	command = self.makeSSH('uname -n')
        
	result = commands.getstatusoutput(command)
	if not result[0] == 0:
            raise Exception("Could not connect to " + self.server)		
        
	return result[1]


    def update(self):
        '''
	Runs the "/usr/local/bin/update -T <train> update"
	through ssh 
	'''
        self.versionControl()

        print "*****************************************"
	print "***      Updating " + self.server
        print "*****************************************"
	print
	logging.info(" **** Updating " + self.server)
        command = self.makeSSH('freenas-update  ' + self.train + ' update')
        print command
	logging.info(command)
	result = True

	self.update_output = commands.getstatusoutput(command)
         
	if not self.update_output[0] == 0:
            result = False
	if not self.parseUpdateOutput(self.update_output[1]):
            result = False

	return result


    def reboot(self):
	'''
	reboot the system 
	'''

	print "***********************************"
	print "**** Rebooting " + self.server
	print "***********************************"
        logging.info(" **** Rebooting " + self.server)
        url = 'http://' + self.server + '/api/v1.0/system/reboot/'
        if self.isUp(): 
            r = requests.post(url, auth = auth, headers = headers)
	# wait until system is up
	while not self.isUp():
            time.sleep(10)

        if not r.status_code == 202:
            
	    return True
         
        return False


    def parseCheckOutput(self, output):
        '''
	Looks for errors
	in the command line output of 
	the "/usr/local/bin/update check" utility
	'''

	result = True
	sig = re.compile('Signature check succeeded')
	no_update = re.compile('DownloadUpdate:  No update available')
        pkg = re.compile('DownloadUpdate:  Will upgrade package ')
	bld = 'Upgrade package '
        error = re.compile('^ERROR')
        sequence = 'Sequence'
	train = 'Train '

        packages = []
	builds = []
	signatureCheck = False
	 
	sequenceLine = ''     # this will be handy in case updater will be changing the trains
        
	print " **** From the output of /usr/local/bin/update check  ****\n"

	for line in output.split('\n'):
            logging.debug(line)     
	    if sig.search(line):
               	signatureCheck = True
            if pkg.search(line):
                packages.append(line.lstrip('DownloadUpdate:  Will upgrade package '))
		print line
            if line.startswith(bld) and line.count('->'):
                builds.append(line)       # keep track of the package names to compare after upgrade		   
		print line
	    if error.search(line):       # TODO: should set result to FALSE?
		logging.exception(line)    
	        
            
            # message about the train changes in log		    
            if line.startswith(train) and line.count('->'):
		logging.info(line)    
                print line                          
            if line.startswith(sequence) and line.count('->'):
		logging.info('*******************')    
		logging.info(line)
		logging.info('********************')
		sequenceLine = line 
		print '****************************************'
		print '\n **** Following update sequence found '
                print line
		logging.info('Update sequence found: ' + line)
		print '****************************************'
		print
	    # Dont trust this, after first download, it reports as no update available	
            if no_update.search(line):
		#self.update_available = False
		#logging.error(line)
		print line
		pass
		    

        print " *****************************************"
        
	if signatureCheck == False:
	    logging.info('signature check failed')	
            result = False
	   
        return result


    def parseUpdateOutput(self, output):
        '''
	parse whole output of the updating
	check for error and other messages
	to accumulate and analyze aferwards
	as part of verification
	'''
	result = True
        umount = re.compile('Unmounted successfully')

        grub = re.compile('GRUB configuration updated successfully')
        activ = re.compile('Activated successfully')
        reboot = re.compile('System should be rebooted now')

        install = re.compile('Installing for i386-pc platform.')
        finished = re.compile('Installation finished. No error reported.')

        error = re.compile('ERROR')
        exc = re.compile('Update got exception during update: ')
	for line in output.split('\n'):
            logging.info(line)	 	
            if error.search(line):
                result = False
		print line
		logging.info(line)
		logging.error(line)
	    if exc.search(line):
		result = False
		logging.error(line)
		print line
	    if finished.search(line):
		logging.info(line)    
	        print line	    
        return result


    def checkSequenceLine(self, sequenceLine):
        w = sequenceLine.split('->')
	print w


    def verifyInstallation(self, version_before, version_after):
	'''
	Verifies the update using 
	/usr/local/bin/freenas-verify
	utility
	'''
	if not version_before <= version_after:
            logging.error('Version before upgrade ' + str(version_before) + ' version after upgrade ' + str(version_after))		
            return False
        
	return True
    

    def printLogNotification(self):
        print "****  For the full output check the file " + os.path.realpath(self.logpath) + " ****"



def verify_through_debug():
    '''
    Use the /usr/local/bin/freenas-debug 
    utility to verify settings
    '''
    return True


def main(argv = None):
    
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
	    help = 'Reboot the system, default:  %default')
        parser.add_option(
	    '--server',  
	    type = "string",
	    default = 'z20ref-a.sjlab1.ixsystems.com',
	    help='Name of the server to be updated, default: %default')
        parser.add_option(
	    '--train',  
	    type = 'string', 
	    help='Train name, default: %default', 
	    default = 'TrueNAS-9.3-Nightlies')
	parser.add_option(
            '--auth', 
            type = 'string',
            help='password, MANDATORY')
	parser.add_option(
            '--user', 
            type = 'string',
            default = 'root',
            help='user, default: %default')
	parser.add_option('--log', 
            type = 'string',
	    default = '',
            help='Path to the log directory, default=%default')
	parser.add_option(
	    '--print_version',  
	    action = 'store_true',
	    default = False,
	    help='Print OS Version string and exit, default: %default')
        
   
        args, rest = parser.parse_args()	
	print "****    Following options are specified " + str(args)

        results = {}
        # create the test class
        test = TestUpdate(args.server, args.train, check = args.check, log = args.log)
	
	
        # if only version is required, exit
	
	version_before = test.software_version()
	results['****   Version check before update'] = version_before

	if args.print_version == True:
            sys.exit(0)
	
	# check for updates
	res = test.checkForUpdates()
	results['Check for updates'] = res
	if args.check == True:
            test.printLogNotification()		
            sys.exit(0)
    
        # update

	res = test.update()
	results['Result of updating the system'] = res

	# TODO: Should this be mandatory?  
	if args.reboot:
	    res = test.reboot()
	    results['Reboot result'] = res
            print " **** Please wait until system is rebooting... **** "
        
	# wait until system is up
	while not test.isUp():
            time.sleep(10)

	# check version after the update
	
	version_after = test.software_version()
        results['Result of version check after update/reboot'] = version_after
         

	# verify the installation
	res = test.verifyInstallation(version_before, version_after)
        results['Verify Installation'] = res

        print "\n **** Results of update ****\n"
	print results
        print
  
        if not False in results:
	    print "****  Server " + str(test.server) + "  successfully updated "	
	    result = True
        else:
            print '****  Test failed '
	    result = False

        test.printLogNotification()
	if not result:
            sys.exit(-1)
        else:
	    sys.exit(0)	
    except Exception, data:
        logging.exception(traceback.print_exc())
	print data
	sys.exit(-1)

if __name__ == '__main__':
	main()

