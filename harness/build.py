import os
import re
import logging
import shutil
import optparse

from collections import OrderedDict

from hvars import shellDir 
from hutils import sh, printlist

__doc__ = """

This module runs builds.
Checks prerequisites,
runs make release,
parses build logs
"""
__usage__ = "python build.py -l /tmp/fnas/freenas"
argparse = optparse.OptionParser(usage = __usage__, version = '%prog 1.0')
logger = logging.getLogger(__name__)


class RunBuild(object):
    def __init__(self, config, branch = 'freenas', target = 'release', clean = True):
        '''
        init for handling builds
	    '''
        self.user      = config['user']
        self.auth      = config['auth']
        self.target    = target
        self.clean     = clean
        self.builddir  = config['builddir']
        self.git       = config['git'] 
        self.steps     = OrderedDict([('setup', False), ('clone', False), ('build', False), ('package', False)])    # just for keeping steps ordered, and hold results until better persistence is there
        
        self.parser    =    ParseResults(self.builddir)
        self.setUp()        

    
    def setUp(self):
        '''
        Set environment
        prepare files and
        directories, check 
        prerequisites
        '''
        if self.clean == True:
            if os.path.isdir(self.builddir):
                shutil.rmtree(self.builddir)
        
        if not os.path.isdir(self.builddir):	
            os.mkdir(self.builddir)
	    
	    # TODO: uncomment when done
	    #os.remove(self.log) 
	    self.sanityCheck()


    def sanityCheck(self):
        '''
        Following packages are necessary:
	
        ports-mgmt/poudriere-devel
        devel/git
        sysutils/cdrtools
        archivers/pxz
        lang/python (2.7 or later, with THREADS support)
        sysutils/grub2-pcbsd
        sysutils/xorriso
        py27-sphinx
        py27-sphinxcontrib-httpdomain-1.2.1 
        (and all the dependencies that these 
        ports/pkgs install, of course)
        '''

        bld_system = os.uname()[3]
        if not bld_system.count('FreeBSD') and not bld_system.count('10'):
            logger.error(bld_system + ' is not suitable for completing build')	
            # TODO: once done, raise exception, cannot build on anywhere else
        curdir = os.getcwd()
        os.chdir(shellDir)
        
        # the script depends on this variable?
        progdir = os.path.join(shellDir, os.pardir)
        os.putenv('PROGDIR', progdir)
        # change later
        if not os.path.exists('./freenas.cfg'):
            shutil.copyfile(os.path.join(os.pardir, 'freenas.cfg.dist'), os.path.join(os.pardir, 'freenas.cfg'))

        res, output = sh('./checkprogs.sh', halt=True)
        
        if not res:
            self.steps['setup'] = False



    def run_shell(self):
        '''
        Run build through 
        build-iso.sh in ix-tests/freenas/scripts 
        TODO: if using this, find better way to itemize
        '''
        os.chdir(shellDir)
        res = sh('./build-iso.sh iso')
        if not res:
            self.steps['setup'] = False
            self.steps['clone'] = False
            self.steps['build'] = False     

    def run(self):
        '''
        Calls
        make release 
        having install.config
        in the build directory
        to get a silent 
        installer
        '''
        self.clone()
        
        self.make_update()
        self.installConfig()
        self.make_release()
        self.report
        
       

    def clone(self):
        '''
        clone git

        '''
        
        if self.clean:
            os.chdir(self.builddir)
            sh('git init')
            res = sh('git clone --depth=1 ' + self.git)
            self.steps['clone'] = res
        if self.git.count('TrueNas'):
                self.steps['git_internal'] = sh('make git internal')      


    def make_update(self):
        '''
        sync git to latest
        '''
        os.chdir(os.path.join(self.builddir, 'freenas'))
        self.steps['make_update'] = sh('make update')	    


    def make_release(self):
        '''
        runs make_release
        '''

        self.steps['make_release'] = sh('make release')	
        
   
    def installConfig(self ):
        '''
        config file for silent
	    installer
	    '''
        with open('install.config', 'w+') as f:
            f.write('password=' + self.auth + '\n')
            f.write('whenDone=reboot'+ '\n')
            f.write('minDiskSize='+ '\n')
            f.write('maxDiskSize='+ '\n')
            f.write('mirror=yes' + '\n')
            f.write('diskcount=5' + '\n')
            f.write('disk=da0' + '\n')
            f.write('upgrade=no' + '\n')


    
    @property
    def result(self):
        '''
        Returns True if 
        all steps were true
        '''
        if False in self.steps.values():
            return False
        return True


    @property
    def report(self):
        '''
        parse release.build.log 
        '''
        s = ''
        s = s + ('Build from repository: ' + str(self.git))
        s = s + ('Clean build: ' + str(self.clean))
        s = s + ('Build result ' + str(self.result))
        if not self.result:
            		
            s = s + ('Build error: ' + str(self.parser.error_msg))
        s = s + ('Package: ' + str(self.steps['package']))
        

        self.parser.parse()
        s = s + self.parser.toString()

        return s




class ParseResults:
    def __init__(self, builddir, shellResult = True):
        '''
        Parse release.build.log
        '''
        self.builddir = builddir    

        self.world  = False
        self.kernel = False
        self.iso    = False
        self.update = False
        self.make   = False
        self.complete = False

        
        self.ports = {}
        self.nano_packages = {}
        self.nano_late_packages = {}

        self.release_dist = False
        self.upgrade_dist = False
        self.log = os.path.join(self.builddir, 'freenas',  'release.build.log')
        
	
        self.buildPassed = shellResult
        self.error_msg = ''


        # keep track  of all logs generated during build
        self.make_log = ''
        self.installworld_log = ''
        self.buildkernel_log = ''
        self.install_log = ''
        self.buildworld_log = ''
        self.etc_log = ''
        self.install_kernel_log = ''
        self.portlog_dir = ''

        self.clean_packages_log = ''
        self.configure_nanobsd_setup_log = ''


    def parse(self):
        print ' **** Parsing  ' + self.log
        if not os.path.exists(self.log):
            print self.log + ' not found'
        with open(self.log) as f:
            rr = f.readlines()
        failed = 'ERROR: build FAILED;'
        passed = 'FreeNAS  build PASSED'

        # get log paths
        for line in rr:
            if line.count(failed):
                self.buildPassed = False    
                print ' **** Build failed, log is ' + self.log    
      	        # find the log and error message
                log =  line.split()[-1]
                self.error_log = log
                self.parseErrorLog(log)
                # No need to proceed most likely...
                break
            if line.count(passed):
               self.buildPassed = True
	       # we can go on finding the logs, etc.
	       

   
    
    def parseSuccess(self):
        '''
 
        '''
        print ' **** Parsing  ' + self.log
        result = False
        with open(self.log) as f:
            rr = f.readlines()
        startlist = [x for x in rr if x.count('Starting build of ')]
        endlist = [x for x in rr if x.count('Finished build of ')]	
        build_kernel = [x for x in rr if x.count('build kernel ')]
        install_kernel = [x for x in rr if x.count('install kernel')]
        nanobsd = [x for x in rr if x.count('nanobsd')]
        failure_message = 'ERROR: build FAILED;'

        passed = [ x for x in rr if x.count('FreeNAS  build PASSED')]
        ref_jail = [x for x in rr if x.count('Creating the reference jail... done')]
        
        #   get log paths
        for line in rr:
            if line.count(failure_message):
                self.buildPassed = False    
                print ' **** Build failed, log is ' + self.log    
                log =  line.split()[-1]
                self.error_log = log
                self.parseErrorLog(log)
                #TODO: you have to parse self.error_log then
                # No need to proceed most likely...
                break

            elif line.count('building make'):
                log = rr[rr.index(line) + 1]
                self.make_log = log.split()[-1]
            elif line.count('run buildworld'):
                log = rr[rr.index(line) + 1]
                self.buildworld_log = log.split()[-1]
            elif line.count(' build kernel '):
                log = rr[rr.index(line) + 1]
     	        self.buildkernel_log = log.split()[-1]
            elif line.count('installworld'):
               	log =  rr[rr.index(line) + 1]
                self.installworld_log = log.split()[-1]
            elif line.count('Starting jail ja-p'):
                log =  rr[rr.index(line) + 1]
                self.portlog_dir = log.split()[-1]
            elif line.count('Creating pkgng repository'):
                pass
            elif line.count('install kernel'):
                install_kernel_log = rr[rr.index(line) + 1]
                self.install_kernel_log = install_kernel_log.split()[-1]
            elif line.count('install /etc'):
                log =  rr[rr.index(line) + 1]
                self.etc_log = log.split()[-1]
            elif line.count('clean_packages'):
                log =  rr[rr.index(line) + 1]
                self.clean_packages_log = log.split()[-1]
            elif line.count('NANO_CUSTOMIZE:'):
                self.nano_packages = line.split()[2:]
            elif line.count('NANO__LATE_CUSTOMIZE:'):
                self.nano_late_packages = line.split()[2:]
		
            elif line.count('configure nanobsd setup'):
                log =  rr[rr.index(line) + 1]
                self.configure_nanobsd_setup_log = log.split()[-1]

      
	assert(len(startlist) == len(endlist))

        if not len(build_kernel) == len(install_kernel):
            self.kernel = False	    	

	if len(passed) == 1:
	   self.buildPassed = True 


        # tracing the ports
	start = []
	end = []
	for p in startlist:
	    	
	    s = p.split()[-1]
            #colors = re.compile(" \x03[0-9]{1,2}(,[0-9]{1,2})?").sub("", s)	
	    # this is not portable, but works to strip the color special characters for this case
	    s = s.replace('\x1b[0;36m', '')
	    s = s.replace('\x1b[0;0m\x1b[0;0m', '')
	    start.append(s)
            self.ports[s] = False
	
	for p in endlist:
            words = p.split()		 
            res = words[-1]
	    pname = words[-2]
	    pname = pname.replace('\x1b[0;36m', '')
            pname = pname.replace('\x1b[0;32m:', '') 
	    
	    end.append(pname)
	    if res.count('Success'):
                self.ports[pname] = True
	    else:
		print p    
	

	# move to reporting
        start.sort()
	end.sort()
	if not start == end:
            self.steps['ports'] = False
        elif not False in self.ports.values():
	    self.steps['ports'] = True
	    

    def parseErrorLog(self, log):
        '''
	compiler specific errors
        call this when sure 
	there is an error line in the 
	log of upper level
	'''
	print '*** Parsing error from log file ' + log
        code_err = ' Error code '
      	err = 'ERROR: build FAILED;'
        self.error_msg  = []
	# find first occurrence of key word in the log 
	# and get the lines above it as error message


        with open(log, 'r') as f:
            lst = f.readlines()
	
	error_lines = []    
	
	for line in lst:
        		
	    if line.count(code_err):
		error_lines.append(lst.index(line)) 
		
	        #print line

	    if line.count(err):
	       msg = lst[lst.index(line) + 1]	    
               print msg

        error_lines.sort()   # smallest index is the first error
	index = error_lines[0] 
	self.error_msg = lst[index -10 : index+1]
	#printlist(self.error_msg)
        return self.error_msg


    def prettyPrint(self):
        print 
	print 'PARSING RESULTS'    
        for k, v in self.__dict__.iteritems():
            print k + '\t\t: ' + str(v)

    def toString(self):
        '''
	generate and return 
	report as a formatted string
	
	'''
	self.report = ''
	self.report = self.report + ('Build kernel: ' + str(self.kernel)+ ' log: ' + self.buildkernel_log + '\n')
	self.report = self.report + ('Build world: ' + str(self.world) + ' log: ' + self.buildworld_log + '\n')
	self.report = self.report + ('Installworld: ' + str(self.world) + ' log: ' + self.installworld_log + '\n')
	
	self.report = self.report + ('Installkernel: ' + str(self.world) + ' log: ' + self.install_kernel_log + '\n')
	self.report = self.report + ('Building ports: \n')
        for k in self.ports.keys():
            self.report =  self.report + ('\t' + str(k) + ':\t' + str(self.ports[k]) + '\n')
        
        return self.report 


    def toFile(self, log):
	'''
	Write report to a file
	'''
        f = open( log, 'w')
	r.write(self.toString())
	f.close()




def main():
    '''
    For testing 
    sync, build, package, report
    '''
    argparse.add_option(
        '-l', '--location',  
        type = "string",
        help='Full path to build directory, mandatory')
    args, rest = argparse.parse_args()
    bld = ParseResults(args.location)
    result = bld.parse()
    bld.prettyPrint()
    print 'OVERALL RESULT'
    print result


if __name__ == '__main__':
    main()	


