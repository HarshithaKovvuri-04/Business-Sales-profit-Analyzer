import requests
import sys

API = 'http://127.0.0.1:8002'

def pretty(j):
    try:
        import json
        return json.dumps(j, indent=2)
    except:
        return str(j)

def main():
    username = 'smoketest_user'
    password = 'TestPass123!'
    role = 'owner'

    print('Registering user...')
    r = requests.post(f'{API}/auth/register', json={'username': username, 'password': password, 'role': role})
    print('Status:', r.status_code)
    try:
        print(pretty(r.json()))
    except:
        print(r.text)

    print('\nLogging in...')
    r = requests.post(f'{API}/auth/login', json={'username': username, 'password': password})
    print('Status:', r.status_code)
    try:
        data = r.json()
        print(pretty(data))
    except Exception as e:
        print('Login failed', r.text)
        sys.exit(1)

    token = data.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    print('\nCreating business...')
    r = requests.post(f'{API}/businesses', json={'name':'Smoke Business','industry':'Testing'}, headers=headers)
    print('Status:', r.status_code)
    try:
        print(pretty(r.json()))
    except:
        print(r.text)

if __name__ == '__main__':
    main()
