import os
import time
import requests
import psycopg2
from urllib.parse import urlparse

API = 'http://127.0.0.1:8002'

def register(username='reg_test', password='TestPass123!', role='owner'):
    r = requests.post(f'{API}/auth/register', json={'username':username,'password':password,'role':role})
    print('status', r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)
    return r

def check_postgres_for_user(dsn, username):
    p = urlparse(dsn)
    conn = None
    try:
        conn = psycopg2.connect(host=p.hostname, port=p.port or 5432, user=p.username, password=p.password, dbname=p.path.lstrip('/'))
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, created_at FROM users WHERE username=%s", (username,))
        rows = cur.fetchall()
        print('rows:', rows)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    r = register('harshitha', 'TestPass123!', 'owner')
    # wait a moment then check postgres
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print('No DATABASE_URL in env')
    else:
        time.sleep(1)
        check_postgres_for_user(dsn, 'harshitha')
