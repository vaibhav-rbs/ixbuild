import json
import requests


r = requests.post(
  'http://10.5.0.171/api/v1.0/storage/volume/1/datasets',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=False,
  data = json.dumps({"name": "newwin2"}

      )
 )

result = json.loads(r.text)
print json.dumps(result, indent=4, sort_keys=True)
print r.reason
print r.status_code


r = requests.post(
  'http://10.5.0.171/api/v1.0/sharing/cifs',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=False,
  data=json.dumps({
    
          "cifs_name": "My Test Share",
          "cifs_path": "/mnt/tank/newwin22"
  })
 )
result = json.loads(r.text)
print json.dumps(result, indent=4, sort_keys=True) 
print r.reason
print r.status_code

