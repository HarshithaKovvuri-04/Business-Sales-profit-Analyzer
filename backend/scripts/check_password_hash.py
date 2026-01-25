import os
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
# read .env
env={}
with open('.env') as f:
    for l in f:
        l=l.strip()
        if not l or l.startswith('#'): continue
        k,v=l.split('=',1)
        env[k.strip()]=v.strip()

p = urlparse(env['DATABASE_URL'])
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432, user=p.username, password=p.password, dbname=p.path.lstrip('/'))
try:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, username, role, password_hash FROM users WHERE username=%s", ('final_test_user',))
    r=cur.fetchone()
    print(r)
finally:
    conn.close()
