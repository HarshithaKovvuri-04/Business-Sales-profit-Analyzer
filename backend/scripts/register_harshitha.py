import requests
API = 'http://127.0.0.1:8002'

payload = {
    'username': 'harshitha',
    'password': 'TestPass123!',
    'role': 'Owner'
}

def main():
    try:
        r = requests.post(f'{API}/auth/register', json=payload, timeout=5)
        print('Status:', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print('Request error:', e)

if __name__ == '__main__':
    main()
