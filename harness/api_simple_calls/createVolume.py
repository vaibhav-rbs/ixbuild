import json
import requests


payload = {
          "volume_name": "lilit",
          "layout": [
                  {
                          "vdevtype": "mirror",
                          "disks": ["da3", "da4"]
                  }
          ]
  }

r = requests.get('http://10.5.0.171/api/v1.0/storage/volume/',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=True)

print r.text


r = requests.post(
  'http://10.5.0.171/api/v1.0/storage/volume/',
  auth=('root', 'abcd1234'),
  headers={'Content-Type': 'application/json'},
  verify=True,
  data = json.dumps(payload)
  )
result = json.loads(r.text)
print json.dumps(result, indent=4, sort_keys=True) 
print r.reason
print r.status_code

