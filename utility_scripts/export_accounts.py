import os, sqlite3
ROOT = os.path.dirname(os.path.dirname(__file__))
DB = os.path.join(ROOT, 'pqr-entertainment', 'tbms.db')
USERS_OUT = os.path.join(ROOT, 'users.txt')
PRODS_OUT = os.path.join(ROOT, 'producers.txt')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT username, role FROM users ORDER BY role, username")
with open(USERS_OUT, 'w', encoding='utf-8') as f:
    for r in cur.fetchall():
        f.write(f"{r['username']}\t{r['role']}\n")

try:
    cur.execute("SELECT p.producer_id, u.username, p.name FROM producers p JOIN users u ON p.user_id=u.user_id ORDER BY p.producer_id")
    rows = cur.fetchall()
except Exception:
    rows = []
with open(PRODS_OUT, 'w', encoding='utf-8') as f:
    for r in rows:
        f.write(f"{r['producer_id']}\t{r['username']}\t{r['name']}\n")

conn.close()
print('Exported to', USERS_OUT, 'and', PRODS_OUT)
