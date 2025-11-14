import os, re, sqlite3

ROOT = os.path.dirname(os.path.dirname(__file__))
DEMO = os.path.join(ROOT, 'demo_credentials.txt')
DB = os.path.join(ROOT, 'pqr-entertainment', 'tbms.db')

SECTION_MAP = {
    'users': 'user',
    'user': 'user',
    'producer': 'producer',
    'producers': 'producer',
    'admin': 'admin',
    'admins': 'admin',
}

def parse_demo(path: str):
    roles = {'admin': set(), 'producer': set(), 'user': set()}
    section = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith('[') and s.endswith(']'):
                tag = SECTION_MAP.get(s[1:-1].strip().lower())
                section = tag
                continue
            if s.startswith('-') and section:
                part = s[1:].strip()
                if ' / ' in part:
                    uname = part.split(' / ')[0].strip()
                else:
                    uname = part
                roles[section].add(uname)
    return roles


def main():
    if not os.path.exists(DB):
        raise SystemExit('DB not found: ' + DB)
    if not os.path.exists(DEMO):
        raise SystemExit('demo_credentials.txt not found')
    roles = parse_demo(DEMO)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute('BEGIN;')
        # Clear schedules entirely
        try:
            cur.execute('DELETE FROM bookings;')
        except sqlite3.Error:
            pass
        try:
            cur.execute('DELETE FROM scheduled_screens;')
        except sqlite3.Error:
            pass

        # Existing users
        cur.execute('SELECT * FROM users')
        existing = {r['username']: r for r in cur.fetchall()}
        allowed = roles['admin'] | roles['producer'] | roles['user']

        # Delete users not in file
        for uname, row in list(existing.items()):
            if uname not in allowed:
                try:
                    cur.execute('DELETE FROM producers WHERE user_id=?', (row['user_id'],))
                    cur.execute('DELETE FROM bookings WHERE user_id=?', (row['user_id'],))
                    cur.execute('DELETE FROM feedbacks WHERE user_id=?', (row['user_id'],))
                    cur.execute('DELETE FROM watchlist WHERE user_id=?', (row['user_id'],))
                except sqlite3.Error:
                    pass
                cur.execute('DELETE FROM users WHERE user_id=?', (row['user_id'],))
                existing.pop(uname, None)

        # Ensure admins
        for uname in roles['admin']:
            row = existing.get(uname)
            if row:
                cur.execute("UPDATE users SET role='admin', password='pass123' WHERE user_id=?", (row['user_id'],))
            else:
                cur.execute("INSERT INTO users (username, password, role, name, email, balance) VALUES (?, 'pass123', 'admin', ?, ?, 0)", (uname, uname.title(), f"{uname}@example.com"))
                cur.execute('SELECT * FROM users WHERE username=?', (uname,))
                existing[uname] = cur.fetchone()

        # Ensure users
        for uname in roles['user']:
            row = existing.get(uname)
            if row:
                cur.execute("UPDATE users SET role='user', password='pass123' WHERE user_id=?", (row['user_id'],))
            else:
                cur.execute("INSERT INTO users (username, password, role, name, email, balance) VALUES (?, 'pass123', 'user', ?, ?, 0)", (uname, uname.title(), f"{uname}@example.com"))
                cur.execute('SELECT * FROM users WHERE username=?', (uname,))
                existing[uname] = cur.fetchone()

        # Ensure producers (exactly these usernames)
        producer_usernames = list(roles['producer'])
        producer_ids = []
        for uname in producer_usernames:
            row = existing.get(uname)
            if not row:
                # create user first
                cur.execute("INSERT INTO users (username, password, role, name, email, balance) VALUES (?, 'pass123', 'producer', ?, ?, 0)", (uname, uname.title(), f"{uname}@example.com"))
                cur.execute('SELECT * FROM users WHERE username=?', (uname,))
                row = cur.fetchone()
                existing[uname] = row
            else:
                cur.execute("UPDATE users SET role='producer', password='pass123' WHERE user_id=?", (row['user_id'],))
            # ensure producer profile
            cur.execute('SELECT * FROM producers WHERE user_id=?', (row['user_id'],))
            prof = cur.fetchone()
            if not prof:
                cur.execute('INSERT INTO producers (user_id, name, details) VALUES (?, ?, ?)', (row['user_id'], uname.replace('_',' ').title(), ''))
                cur.execute('SELECT * FROM producers WHERE user_id=?', (row['user_id'],))
                prof = cur.fetchone()
            producer_ids.append(prof['producer_id'])

        # Delete any other producers
        if producer_ids:
            qmarks = ','.join('?' for _ in producer_ids)
            cur.execute(f'DELETE FROM producers WHERE producer_id NOT IN ({qmarks})', producer_ids)
        else:
            cur.execute('DELETE FROM producers')

        # If a single producer exists, link all movies
        cur.execute('SELECT producer_id FROM producers LIMIT 1')
        row = cur.fetchone()
        if row:
            cur.execute('UPDATE movies SET producer_id=?', (row['producer_id'],))

        cur.execute('COMMIT;')
        print('Sync completed.')
    except Exception as e:
        cur.execute('ROLLBACK;')
        print('Error:', e)
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
