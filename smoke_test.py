import json
from urllib import request, error

BASE='http://127.0.0.1:8002'

def post(path, data, token=None):
    url = BASE+path
    data_b = json.dumps(data).encode('utf-8')
    req = request.Request(url, data=data_b, headers={
        'Content-Type':'application/json',
        **({'Authorization':f'Bearer {token}'} if token else {})
    })
    try:
        with request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), json.load(resp)
    except error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}

if __name__=='__main__':
    username='smoketest_user'
    password='TestPass123!'
    print('Registering user...')
    code, res = post('/auth/register', {'username':username,'password':password,'role':'owner'})
    print('REGISTER:', code, res)

    print('Logging in...')
    code, res = post('/auth/login', {'username':username,'password':password})
    print('LOGIN:', code, res)
    token = res.get('access_token') if isinstance(res, dict) else None

    if not token:
        print('No token, aborting business creation')
    else:
        print('Creating business...')
        code, res = post('/businesses', {'name':'SmokeBiz','industry':'Testing'}, token=token)
        print('CREATE BUSINESS:', code, res)
