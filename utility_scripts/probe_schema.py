import sqlite3, os
p = os.path.join(os.path.dirname(__file__), 'tbms.db')
conn = sqlite3.connect(p)
cur = conn.cursor()
for t in ['producers','movies','events','scheduled_screens','theatres','users','employees']:
    try:
        cur.execute(f'PRAGMA table_info({t});')
        print(f'\n{t}:')
        for row in cur.fetchall():
            print(row)
    except Exception as e:
        print(f'\n{t}: ERR {e}')
conn.close()
