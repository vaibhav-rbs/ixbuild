import optparse
import os
import sys
import traceback
import json
import logging

import htester
import build
import report



__doc__ = """
This script is the main module for starting test harness.
The command to run is:
    python runHarness.py

Run:
    python runHarness.py --help 

for all options.
If no command line options are specified, the defaults will be passed.
The running options can be set from json format config file 
or from command line options.
The command line options will override config file information.

"""

__usage__ = "python %prog% [--build --install --testlist testSuite1 testSuite2] "

parser = optparse.OptionParser(usage = __usage__, version = '%prog 1.0')
logger = logging.getLogger(__name__)



def main():
    '''
    Main entry point of harness
    '''
    reportlog = ''
    try:
        
        parser.add_option(
  	    '--sync',  
	    action='store_true',
	    default = True,
	    help='Sync to head, default:   %default')
        parser.add_option(
        '--build',  
        action='store_true', 
        default = True,
        help = 'Run "make release", default:  %default')
        parser.add_option(
        '--logs',  
        type = "string",
        default = os.path.join('/tmp/logs'),
        help='Full path to directory for output logs, default: %default')
        parser.add_option(
        '--train',  
        type = 'string', 
        help='Train name, default: %default', 
        default = 'TrueNAS-9.3-Nightlies')
        parser.add_option(
        '--jenkins', action='store_true',
        default = True,
        help='Indicates it is running through Jenkins, default: %default')
        parser.add_option(
            '--email', action='store_true',
        default = False,
        help='Send out email to a list from config file, default: %default')
        parser.add_option(
        '--config',  
        type = 'string', 
        help='branch name, default: %default', 
        default = 'harness.config')
        parser.add_option(
        '--noclean',  
        action = 'store_true',
        default = False, 
        help=', default: %default' )
        parser.add_option(
        '--debug',  
        action = 'store_true',
        default = False, 
        help=', default: %default', 
        )

         # parse command line          
        args, rest = parser.parse_args()	
        
        # set debug logs
        if args.debug == True:
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)

        reportlog = os.path.join(args.logs, 'Report.txt')  
     
        
        print "****    Following harness options are specified " + str(args)
        # read config file
        config = json.load(file(args.config))
        
        r = report.Reporter(reportlog)    
        if args.build == True:
            bld = build.RunBuild(config)
            r.setBuildInfo(bld)
            bld.run()
            
        # create the tester class
        test = htester.Tester(config)
        r.setTestInfo(test)
	
        if args.email == True:
            r.emailReport()		
        print r.result

    except Exception, data:
        logger = logging.getLogger()
        print dir(traceback)
        if logger.level == logging.DEBUG:
            logging.error(traceback.print_exc())

        traceback.print_exc()
        print(' **** Harness run failed, for details check the log: ' + reportlog)    
        exit(-1)
    else:
        print(' **** Harness run complete, for results check the log: ' + reportlog)
        exit(0)    



if __name__ == '__main__':
	main()
	
