import os
from urllib.parse import urlparse
import psycopg2

# read .env
env = {}
with open('.env') as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith('#'):
            continue
        k,v=line.split('=',1)
        env[k.strip()]=v.strip()

dsn = env.get('DATABASE_URL')
if not dsn:
    print('No DATABASE_URL in .env')
    raise SystemExit(1)

p = urlparse(dsn)
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432, user=p.username, password=p.password, dbname=p.path.lstrip('/'))
try:
    cur = conn.cursor()
    for uname in ('final_test_user','harshitha','smoketest_user','smoketest_user2','smoketest_user3'):
        cur.execute("SELECT id, username, role, created_at FROM users WHERE username=%s", (uname,))
        rows = cur.fetchall()
        print(uname, 'rows:', rows)
finally:
    conn.close()
