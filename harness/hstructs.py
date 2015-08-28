harness_root = ''
log = ''
build_log = 

vservers = {}
servers = {}

hconfig = {}

testlist = {
'build' : {'command' : 'make build.sh', 'directory' : '', 'log' : 'release.build.log'},
'smoke_test1': { 'command' : './9.3-tests.sh', 'directory' : '', 'servers' : ['10.5.0.43'] 
'update_software': {'command' : 'python update_software.py', 'directory' : '', 'servers' : [['z20ref-a.sjlab1.ixsystems.com','z20ref-b.sjlab1.ixsystems.com'],'10.5.65.32']

}
