import requests

try:
    r = requests.get('http://localhost:5000/')
    print(r.status_code)
    if(r.status_code!=200):
        exit(1)
    print(r.text)
except:
    exit(1)