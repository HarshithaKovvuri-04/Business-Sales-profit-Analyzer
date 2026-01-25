import sqlite3
import sys
path = r'c:\Users\SAMA\Desktop\InfoAssignment1\backend\dev.db'
conn = sqlite3.connect(path)
cur = conn.cursor()
try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cur.fetchone():
        print('no users table')
        sys.exit(0)
    rows = list(cur.execute('select id,username,role,created_at from users').fetchall())
    print('users:', rows)
except Exception as e:
    print('err', e)
finally:
    conn.close()
