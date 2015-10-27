import os
import re
import time
import logging
import shutil
import optparse
import HTMLgen

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
    def __init__(self, builddir, html_output, debug):
        '''
        Parse release.build.log
        '''
        # top directory of build, 
        self.builddir = builddir
        self.debug = debug 
        self.html_output = html_output  

        self.ports = {}
        self.steps = {}

        # RESULTS
        self.buildPassed = False
        self.build_result = False
 
        # KNOWN ISSUES, pair of error message: reason
        self.known_issues = {'No space left on device': 'Build directory full'}

        # KNOWN LOGS
        self.buildlog = os.path.join(self.builddir, '_BE',  'release.build.log')
        self.main_logdir = os.path.join(self.builddir, '_BE/objs/logs')
        self.port_log_dir = os.path.join(self.builddir, '_BE/objs/ports/logs/bulk/ja-p/latest/logs')
        self.port_error_dir = os.path.join(self.builddir, '_BE/objs/ports/logs/bulk/ja-p/latest/logs/errors')

        self.buildworld_log = os.path.join(self.builddir, '_BE/objs/logs/buildworld')
        self.installworld_log = os.path.join(self.builddir, '_BE/objs/logs/jail-installworld')
        self.buildkernel_log = os.path.join(self.builddir, '_BE/objs/logs/buildkernel')
        self.installkernel_log = os.path.join(self.builddir, '_BE/objs/logs/jail-installkernel')
        self.distribution_log = os.path.join(self.builddir, '_BE/objs/logs/jail-distribution')
        self.gui_log = os.path.join(self.builddir, '_BE/objs/logs/build-gui')
        self.pkgtools_log = os.path.join(self.builddir, '_BE/objs/logs/build-pkgtools')
        self.htmlpages = os.path.join(self.builddir, '_BE/objs/world/usr/local/www/data/docs/html')
        self.pkg_install_log = os.path.join(self.builddir, '_BE/objs/logs/pkg-install')

        self.collected_logs = []
        self.failed_port_logs = []
        self.clean_packages_log = ''


        # HTML reports from those logs
        self.html_logs = html_output
        self.html_report = os.path.join(self.html_logs, 'build_report.html')
        self.html_error = os.path.join(self.html_logs, 'error_message.html')  

        # ALL KNOWN PHRASES
        self.failure_phrase = 'ERROR: '
        # if this is found, supposedly everything went well
        self.success_phrase = 'build succeeded, ' 
        self.port_start_phrase = 'Starting jail ja-p'
        self.build_environment_phrase = 'Build environment is OK'

        # index of useful messages
        self.port_start_index = 0

        # lists 
        self.warnings = []
        # will use for html report
        self.error_to_html = []
        self.failure_reason = ''

        self.build_world  = {'name': 'build_world', 'result': False, 'log': self.buildworld_log }
        self.install_world = {'name': 'install_world', 'result': False, 'log': self.installworld_log} 
        self.build_kernel = {'name': 'build_kernel', 'result': False, 'log': self.buildkernel_log }
        self.install_kernel = {'name': 'install_kernel', 'result': False, 'log': self.installkernel_log }
        self.distribution = {'name': 'distribution', 'result': False, 'log': self.distribution_log }
        self.ports = {'name': 'ports', 'result': False, 'log': self.port_log_dir }
        self.gui = {'name' : 'gui', 'result': False, 'log': self.gui_log}
        self.iso    = {'name': 'iso', 'result': False, 'log': ''}
        self.package_install = {'name': 'package_install', 'result': False, 'log': self.pkg_install_log}

        # try to compute from logs
        self.faulty_log = None 

        # the order matters, most likely
        self.stages = [
            self.build_world, 
            self.install_world, 
            self.build_kernel, 
            self.install_kernel,
            self.distribution,
            self.ports,
            self.gui,
            self.package_install,
            self.iso ]

        self.setUp()

 
    def setUp(self):        
        # cleanup goes here
        if os.path.exists(self.html_logs):
           shutil.rmtree(self.html_logs)
        os.mkdir(self.html_logs)     

    
    def parse(self):
        '''
        build.release.log parser
        '''
        result = True
        error = re.compile('ERROR: ')
        lines = self.readTopLog()
        
        for line in lines:
            if error.search(line):
                self.parseFailure(lines, lines.index(line))
                return False
            elif line.count('WARNING'):
                self.warnings.append(line)
            elif line.count(self.port_start_phrase):
                self.port_start_index = lines.index(line)
            elif line.count(' Log file: '):
                self.collected_logs.append(line.split()[-1])        
            elif line.count(self.success_phrase):
                for stage in self.stages:
                    stage['result'] = True
                self.build_result = True    
                print "Looks like build has gone to the end!!!" 
                   
        return result                 

    def parseFailure(self, lines, index):
        '''
        Parse knowing the faulty line
        '''
        # keep track of ports
        ports = self.track_ports(lines)  
        faulty_log = ''
        start = 0      
        if index >= 20:
            start = index - 20
            
        for line in lines[start:index+1]:
            # this is for html file
            self.error_to_html.append(line)    
            # lets see if we can figure out if this is a known issue
            for known in self.known_issues.keys():
                if line.count(known):
                    self.failure_reason = self.known_issues[known]
        
        # First try is to find the log on the error line
        if lines[index].count(' log '):
            self.faulty_log = lines[index].split()[-1]
        #print self.faulty_log
        # Try to search in reverse order. chance is 
        # the first log is the failure usually
        for line in reversed(lines[start:index+1]):
            if line.count('Log '):
                # we can make use of the logs:
                #print line
                self.collected_logs.append(line.split()[-1])


    def toHTML(self):
        # Top HTML document
        doc = HTMLgen.SimpleDocument(title='index')

        # HEADER
        text = HTMLgen.Heading(1, 'Build Result: ' + str(self.build_result))
        doc.append(HTMLgen.Paragraph(text))
        text = HTMLgen.Text('Build date: ' + str(time.strftime("%c")))
        doc.append(HTMLgen.Paragraph(text)) 

        # FAILING LOGS
        if not self.build_result:
            if self.failure_reason:
                text = HTMLgen.Text('Known Reason: ' + str(self.failure_reason))
                doc.append(HTMLgen.Paragraph(text))

            doc.append(HTMLgen.Paragraph('Please check these logs for details:'))
            
            if self.failed_port_logs:
                for log in self.failed_port_logs:
                    newpath = self.file_to_html(log)
                    href = HTMLgen.Href(newpath, HTMLgen.Paragraph(HTMLgen.Text(log)))
                    doc.append(HTMLgen.Paragraph(href))
                    
            else:
                href = HTMLgen.Href(self.faulty_log, HTMLgen.Text("Top failing log: " + str(self.faulty_log)))
                doc.append(HTMLgen.Paragraph(href))

        #ERROR MESSAGE
        doc_message = HTMLgen.SimpleDocument(title='error snippet')
        lst = HTMLgen.List()
        for line in self.error_to_html:
            lst.append(line)
        doc_message.append(lst)
        doc_message.write(self.html_error)
        
        # reference from main doc
        href = HTMLgen.Href(self.html_error, HTMLgen.Text("Error Message in " + self.buildlog ))    
        doc.append(href)

        doc.append(HTMLgen.Paragraph('Build logs:'))
        #print self.collected_logs
        for log in self.collected_logs:
            ###########REMOVE NEXT LINE LATER
            if self.debug:
                log = log.replace('storage', 'tmp')
            if os.path.exists(log):
                newpath = self.file_to_html(log)
                href = HTMLgen.Href(newpath, HTMLgen.Paragraph(HTMLgen.Text(log)))
                doc.append(href)
       
        # commit to log
        doc.write(self.html_report)

        '''
        # TODO: should compare the logs directory with collected logs 
        for fl in self.collected_logs:
            ###########REMOVE NEXT LINE LATER
            fl = fl.replace('storage', 'tmp')
            #doc = HTMLgen.SimpleDocument(title=fl)
            
            lst = HTMLgen.List()
            if os.path.exists(fl):
                for line in open(fl, 'r').readlines():
                    lst.append(line)
                ff = os.path.split(fl)[1]
                print ff
                newpath = os.path.join(self.html_logs, ff +'.html')
                print newpath
                doc.write(newpath)
            
            if os.path.exists(fl):
                newpath = self.file_to_html(fl)
        ''' 
               

    def file_to_html(self, f_path):
        doc = HTMLgen.SimpleDocument(title=f_path)
        lst = HTMLgen.List()
        # TEMPORARY
        f_path = f_path.replace('storage', 'tmp')
        if os.path.exists(f_path):
            for line in open(f_path, 'r').readlines():
                lst.append(line)
        doc.append(lst)
        new_path = os.path.join(self.html_logs, os.path.split(f_path)[1] + '.html')
        doc.write(new_path) 
        return os.path.join(new_path)       

    def track_ports(self, lines):
        '''
        '''
        print 'Tracking ports'
        start = re.compile('Starting/Cloning builders')
        stop = re.compile('Stopping builders')
        for line in lines:
            if line.count('Failed ports: '):
                print line
 
        for f in os.listdir(self.port_error_dir):
            self.failed_port_logs.append(os.path.join(self.port_error_dir, f))      
        #print self.failed_port_logs


    def parse_port_log(self, lines, log):
        '''
        This will be harder to parse
        but may be the start
        '''
        syntax = 'SyntaxError: invalid syntax'
        errors = {log: [], 'lines' : []}
        for line in lines:
            if line.count(syntax):
                 errors[log].append(line)
                 errors['lines'].append(lines.index(line))
        return errors  

    def readTopLog(self):
        '''
        Read release.build.log 
        and return list of lines
        '''
        with open(self.buildlog) as f:
            lines = f.readlines()
            return lines

    def prettyPrint(self):
        print 
        print 'PARSING RESULTS'    
        for k, v in self.__dict__.iteritems():
            print k + '\t\t: ' + str(v)

def main():
    '''
    For testing 
    sync, build, package, report
    '''
    argparse.add_option(
        '-l', '--location',  
        type = "string",
        help='Full path to build directory, mandatory')
    argparse.add_option(
        '--html_logs',  
        type = "string",
        default = './htmllogs',
        help='Output directory for html logs, default %default'),

    argparse.add_option(
        '-d', '--debug',  
        action = "store_true",
        default = False,
        help='Print out debug information, default: %default')
    argparse.add_option(
        '-c', '--clean',  
        action = "store_true",
        default = False,
        help='Clean build, default: %default')
    args, rest = argparse.parse_args()
    bld = ParseResults(args.location, args.html_logs, args.debug)
    result = bld.parse()
    if args.debug:
        bld.prettyPrint()
    bld.toHTML()
    print 'OVERALL RESULT'
    print result
    return result


if __name__ == '__main__':
    main()	


