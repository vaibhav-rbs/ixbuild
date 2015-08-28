import json
import requests
import traceback
import optparse
import os
import sys
import logging

import hutils

__doc__ = '''
 
 This calls FreeNAS and TrueNas REST api-s 
 
 Run the script with --help for all the available options

 If --api option omitted, call to get() on all api from the API_LIST structure
 in this module and dump the return into a log files named after the api. 
 For calling specific api, pass  --api is passed, followed with api path. Example:
 python %prog --api system/advanced
 
 The return value is saved to .json file
 The created .json file can be loaded for further use.
 status.txt is lists the result of each call 

 For calling put and post, --dataset option should be passed. 
 TODO: change to accept dataset from a file as well as command line

 getId() will return the id of the object having its name, 
 for example, getId('igb0') can return integer value of 2


example usage: python api_list.py --api /system/information --server 10.22.34.22 


TODO: read dataset from file in addition to command line


'''


__usage__ = '''%prog --api = <APIPATH> --user=<ROOT> auth = <PASSWORD> call = <APITYPE> --dataset="{}"

Examples: 
    python api_list.py --api account/users/3 --call get --server 10.6.65.111 --user root auth 12345678
    python api_list.py --api account/users/1002 --call post --dataset="{'bsd_user_full_name' : 'a user'}" --user root --auth qwerty --server 10.5.0.198
    python api_list.py --api account/users/1002 --call delete
'''

parser = optparse.OptionParser(usage = __usage__, version = '%prog 1.0')


headers = hutils.headers()

codes = { 'get' : 200, 
        'delete' : 204, 
        'put' : 200, 
        'post' : 201, 
        'not_found' : 404, 
        'methond_not_allowed' : 405, 
        'conflict' : 409 
        }


API_LIST = {
    'system' : ['advanced', 'alert', 'bootenv', 'bootenv/prechanges', 
    'email', 'ntpserver', 'ntpserver/id', 'settings', 'ssl', 'tunable', 'tunable/id', 'version', ],
    
    'network' : [ 'globalconfiguration', 'interface', 'interface/id', 'vlan', 'vlan/id', 'lagg', 'staticroute', ],
    
    'services' : ['services', 'services/cifs', 'afp', 'cifs', 'domaincontroller', 
    'dynamicdns', 'ftp', 'iscsi/globalconfiguration', 'iscsi/extent', 'iscsi/extent/id', 
    'iscsi/authorizedinitiator', 'iscsi/authcredential', 
    'iscsi/authcredential/id', 'iscsi/target', 'iscsi/targettoextent','iscsi/targettoextent/id',
     'iscsi/portal', 'iscsi/portal/id', 'ssh', 'tftp', 'ups', 'service/ssh'],

    'account' : ['bsdusers', 'users', 'users/id', 'groups', 'groups/id', 'users/password'],
    'directoryservice' : ['activedirectory', 'ldap', 'nis', 'nt4', 'idmap/ad', 'idmap/adex', 
    'idmap/adex/id', 'idmap/hash', 'idmap/hash/id', 'idmap/ldap', 'idmap/ldap/id', 'idmap/nss', 
    'idmap/nss/id', 'idmap/rfc2307', 'idmap/tdb', 'idmap/tdb2',],

    'jails': ['configuration', 'jails', 'start', 'stop', 'restart', 'mountpoints', 
    'templates', 'templates/id', ],

    'plugins' : ['plugins', 'plugins/id', 'plugins/id/stop', 'plugins/id/start', ],


    'sharing' : ['cifs', 'cifs/id', 'nfs', 'nfs/id', 'afp', 'afp/id'],

    'storage' : ['volume', 'volume/id', 'volume/id/datasets', 'volume/id/datasets', 
    'volume/id/scrub', 'volume/id/upgrade', 'volume/id/upgrade', 
    'volume/id/replace', 'volume/name/replace', 'volume/name/detach', 
    'volume/id/detach', 'volume/id/recoverykey', 'volume/id/unlock', 
    'volume/name/unlock', 'volume/id/status', 'volume/name/status', 
    'snapshot', 'snapshot/id', 'snapshot/tanki@test, ''snapshot/tank%2Ftest', 
    'snapshot/tank%2Ftest/clone', 'task', 'task/id', 'replication', 
    'replication/0', 'scrub', 'scrub/id', 'disk', 'disk/id', 'permission', ],

    'tasks' : ['cronjob', 'cronjob/0', 'cronjob/id/run', 'initshutdown', 
    'initshutdown/id', 'rsync', 'rsync/id', 'rsync/id/run', 'smarttest','smarttest/id' ],

    'failover': ['failover', 'failover/pairing-create'],

    }


get_none = { 'account' : [ 'users/0/password', ], 'system' : ['reboot'] }
doNotPost = { 'account' : ['users/0/password',], 'system' : ['reboot']}


doNotGet = ['system/reboot', 'system/shutdown']
doNotDelete = []
doNotPost = []
doNotPut = []



def put(url, auth, dataset, log_status, log_out):
    '''
    call put()
    '''

    print '\n **** Updating ' + url + ' with dataset: ' + str(dataset)
    
    print " **** Calling PUT, " + str(url) + "  with dataset " + str(dataset)	
    r = requests.put(url=url, auth=auth, data = json.dumps(dataset), headers = headers)

    if r.status_code == codes['put']:
        print 'Update ' + url + ' --> Succeeded!'
        result = json.loads(r.text)

        print json.dumps(result, indent = 4, sort_keys = True)
    else:
        print r.text    
        print 'Update ' + url + ' --> Failed with status: ' + str(r.status_code)
        print 'With reason ' + str(r.reason)
    return r.status_code, r.text



def post(url, auth, dataset, log_status = sys.stdout, log_out = sys.stdout):
    '''
    Update existing setting with dataset

    '''

    logging.debug( '\n **** Calling POST,  ' + url + ' with dataset: ' + str(dataset))
    logging.debug(dataset) 
    result = ''
 
    r = requests.post(url=url, auth=auth, data = json.dumps(dataset), headers = headers)
    #logging.debug(json.dumps(r.text))   
    if r.status_code == codes['post']:
        logging.debug( 'Create ' + url + ' --> Succeeded!')
	result = json.loads(r.text)
	logging.debug(json.dumps(result, indent = 4, sort_keys = True))
    else:
        print 'Create ' + url + ' --> Failed with status: ' + str(r.status_code)
        print "The reason for failure is " + str(r.reason)       
    return r.status_code, result
    
	


    	
def delete(url, auth, dataset = None, log_status = sys.stdout, log_out = sys.stdout):
    '''
    delete existing setting
    returns status and return dataset
    input dataset ignored
    '''
    r = requests.delete(url=url, auth=auth, data = json.dumps(dataset), headers = headers)
    if r.status_code == codes['delete']:
        logging.debug("Delete " + url + ' --> Succeeded!')
	print r.text
    else:
        logging.error('Delete ' + url + ' --> Failed with status: ' + str(r.status_code))
        logging.error( "The reason for failure is " + str(r.reason) )
    return r.status_code, r.text    
	

def get(url, auth, dataset = None, log_status = sys.stdout, log_out = sys.stdout):
    '''    
    get existing value of setting
    dataset is ignored
    '''
    print '\n****   Getting ' + url + ' ......'
    r = requests.get(url=url, auth=auth)
    
    result = '' 
    	
    if r.status_code == 200:
        	  
        try:
            result = json.loads(r.text)
            #f_out.write('\n' + '#' + url + '\n')
            logging.info('\n' + '#' + url + '\n')

            logging.debug('Get ' + url + ' --> Succeeded!')
            # send result to file
            
            #json.dump(result, f_out, indent = 4, sort_keys = True)
	     
            logging.info(json.dumps(result, indent=4, sort_keys=True))    
            logging.error('\n **** Get ' + url + ': ' + str(r.status_code) + ' succeeded!\n')  

        except ValueError, data:
            traceback.print_exc()	    
            logging.error( " **** Could not load json data for the reason: " + str(r.reason)) 
	    
	    
            logging.error(url + ' : ' + str(data))
	
    else:
        logging.error( '****  Get ' + url + ' --> Failed with code ' + str(r.status_code) + ' for reason ' + str(r.reason))
    
    return r.status_code, result 


    	
def getId(url, auth, name, dataset = None):
    '''
    helper that returns the id
    of a taking the name of 
    unit, whatever it is,
    and the url, for example, the id
    of interface named igb0
    '''
    result, text  = get(url, auth)
    r_id = None
    # better check for type 
    # in case something changes 
    # in api in the future
    if isinstance(text, list):  # iterate the list of dicts
        for unit in text:
            for k in unit.keys():
                if unit[k] == name:
                    r_id = unit['id']
    elif isinstance(text, dict):
        for k in text.keys():
	    if text[k] == name:
	        r_id = text['id']
    else:
        print "List or dict was expected"    
    print 'Returning ' + str(r_id)		
    return r_id
    	    
def getIds(url, auth, dataset = None):
    '''
    helper that returns the 
    list of all id-s
    This is useful 
    when id-s do not start
    with 0, for example
    '''
    result, text  = get(url, auth)
    r_ids = []
    # better check for type 
    # in case something changes 
    # in api in the future
    if isinstance(text, list):  # iterate the list of dicts
        for unit in text:
            for k in unit.keys():
                if unit[k] == name:
                    r_ids.append(unit['id'])
    elif isinstance(text, dict):
        for k in text.keys():
            if text[k] == name:
                r_id.append(text['id'])
    else:
        print "List or dict was expected"    
    print 'Returning ' + str(r_id)      
    return r_id


def getAll(auth, server, log_status = sys.stdout, log_out = sys.stdout):
    '''
    Calls get() on all known 
    API list 
    '''
    for key in API_LIST.keys():
        for api in API_LIST[key]:
        
            line = key + '/' + api	
            url = hutils.make_url(server, line)
            log_tmp, ext = os.path.splitext(log_out)
            # create a file name that has the name of the api, so that separate file is created for call
            log_api = log_tmp + '_' + line.replace('/', '_') + ext
            get(url, auth, log_status, log_api)


def callApi(auth, server, log_status=sys.stdout, log_out=sys.stdout, name = None, operation = 'get', dataset = None):
    '''
    need to parse the
    entry string, find it
    in the whole api list
    and create the url
    '''
    op = globals()[operation]
    url = hutils.make_url(server, name)

    op(url, auth, log_status=log_status, log_out=log_out, dataset=dataset)



def getApiReturn(js_out):
    '''
    Returns the json object
    of the api's get retun value
    of r.text
    '''
    return json.loads(js_out.text)
    

def dump(data, log_out = sys.stdout):
    '''
    Loads and prints json object formatted in 
    standard way
    '''
    json.dump(data, log_out, indent = 4, sort_keys = True)


def prettyPrint(dataset):
    '''
    Use to print json nicely
    '''
    print json.dumps(result, indent = 4, sort_keys = True)
 
             
def main():
    '''
    main entry point, enables
    running this script standalone, 
    and parses command line
    options
    '''
    parser.add_option(
    '--api', type='string',
    help='Full path to the API, example: account/groups/1',
    default = '')
       
    parser.add_option('--call', 
    default = 'get', 
    help='call, one of get, put, post, delete')
    parser.add_option('--user', 
    default = 'root', 
    type = 'string',
    help='User, default: %default')
    parser.add_option('--auth', 
    type = 'string',        
    help='Secret, MANDATORY',
    default = 'abcd1234'         # remove later
    )
    parser.add_option(
    '--server',  
    type = 'string',
    default = 'z20ref-a.sjlab1.ixsystems.com',
    help='Remote server to connect to, default: %default')
    
    parser.add_option(
    '--dataset',  
    type = 'string',
    default = '{}',
    help='Dataset passed as a string, for put or post calls, default: %default')

    
    args, rest = parser.parse_args()
    auth = hutils.make_auth(args.user, args.auth)
    
    common_url = hutils.make_common_url(args.server)
    logdir = os.path.join(os.getcwd(), 'api_logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)	    
    output = os.path.join(logdir, args.server + '_' + args.api.replace('/', '_') + '_output.json')
    status = os.path.join(logdir, args.server + '_status.txt')


    if os.path.exists(status):
        os.remove(status)
    if os.path.exists(output):
        os.remove(output)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')

 
    fout = logging.FileHandler(output)
    fout.setLevel(logging.INFO)
    fout.setFormatter(formatter)
    
    
    fstatus = logging.FileHandler(status)
    fstatus.setLevel(logging.ERROR)
    fstatus.setFormatter(formatter)

    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)

    logger.addHandler(fout)
    logger.addHandler(fstatus)
    logger.addHandler(stream)


    logging.debug('DEBUG MESSAGE')
    logging.error('ERROR MESSAGE')
    
    if not args.api:
        getAll(auth, args.server, log_status = status, log_out=output)
    else:
         
        print status
        print output   
        #callApi(auth, args.server, log_status=status, log_out=output, name = args.api, operation = args.call, dataset = args.dataset)    
        callApi(auth, args.server, name=args.api, operation=args.call, dataset=args.dataset)
    

    print " **** Logs generated as " + output
    print " **** Logs generated as " + status



if __name__ == '__main__':
    main()	
