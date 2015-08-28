import json
import requests

r = requests.post(
  'http://10.5.0.171/api/v1.0/account/users/',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=True,
  data=json.dumps({
       'bsdusr_uid': '1100',
       'bsdusr_username': 'myuser',
       'bsdusr_mode': '755',
       'bsdusr_creategroup': 'True',
       'bsdusr_password': '12345',
       #'bsdusr_shell': '/usr/local/bin/bash',
       'bsdusr_full_name': 'Full Name',
       #'bsdusr_email': 'lilit@ixsystems.com',
   })
 )
print r.text
print r.reason
