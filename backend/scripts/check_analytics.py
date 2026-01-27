import requests, json
API='http://127.0.0.1:8002'
# login to get token
USERNAME='smoketest_user'
PASSWORD='TestPass123!'
def get_token():
    r=requests.post(API+'/auth/login', json={'username':USERNAME,'password':PASSWORD}, timeout=10)
    if r.status_code!=200:
        print('Login failed', r.status_code, r.text)
        return None
    return r.json().get('access_token')

token = get_token()
if not token:
    raise SystemExit('No token')
headers={'Authorization':f'Bearer {token}'}
paths=['/analytics/charts/5','/analytics/monthly/5','/analytics/profit/5','/analytics/profit_trend/5']
for path in paths:
    try:
        r=requests.get(API+path, headers=headers, timeout=10)
        print('PATH',path,'STATUS',r.status_code)
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)
    except Exception as e:
        print('PATH',path,'ERROR',e)
