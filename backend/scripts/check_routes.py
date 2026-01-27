import requests
print('root', requests.get('http://127.0.0.1:8002/').status_code, requests.get('http://127.0.0.1:8002/').json())
print('health', requests.get('http://127.0.0.1:8002/health').status_code, requests.get('http://127.0.0.1:8002/health').json())
r=requests.get('http://127.0.0.1:8002/routes')
print('routes', r.status_code)
js=r.json()
print('routes count', len(js))
for i in js[:40]:
    print(i)
