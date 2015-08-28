import json
import requests

r1 = requests.get(  'http://10.5.0.171/api/v1.0/sharing/cifs/',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
)

result = json.loads(r1.text)
print json.dumps(result, indent=4, sort_keys=True)

r = requests.post(
  'http://10.5.0.171/api/v1.0/sharing/cifs/',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=False,
  data = json.dumps({
      'cifs_path': '/mnt/block2/windataset/', 
      'cifs_name': 'cifsshare',
      "cifs_vfsobjects": [
            "aio_pthread", 
            "streams_xattr"
        ], 

      }
   )
 )

print dir(requests)
result = json.loads(r.text)
print type(result)

print dir(result)
print json.dumps(result, indent=4, sort_keys=True) 
print 'The reason is ' + str(r.reason)
print 'The status code is: ' + str(r.status_code)

