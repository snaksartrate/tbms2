import argparse
import json
import os
import sqlite3
import sys
from typing import Any


def resolve_db(path_arg: str, here: str) -> str:
    if os.path.isabs(path_arg):
        return path_arg if os.path.exists(path_arg) else ''
    cands = [
        os.path.abspath(path_arg),
        os.path.join(here, path_arg),
        os.path.join(here, os.path.basename(path_arg)),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return ''


def ensure_admin(conn: sqlite3.Connection, username: str, password: str, name: str, email: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        uid = int(row[0])
        cur.execute("UPDATE users SET password=?, role='admin', name=?, email=? WHERE user_id=?", (password, name, email, uid))
        return uid
    cur.execute(
        "INSERT INTO users (username, password, role, name, email, balance) VALUES (?,?,?,?,?,0)",
        (username, password, 'admin', name, email),
    )
    return int(cur.lastrowid)


def clear_bookings(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) FROM bookings')
        count = int(cur.fetchone()[0])
    except sqlite3.Error:
        return 0
    cur.execute('DELETE FROM bookings')
    return count


def unbook_in_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            lk = k.lower()
            if lk in ('booked', 'isbooked', 'reserved', 'is_reserved', 'is_resvd'):
                new[k] = False
            elif lk in ('booked_by', 'user_id', 'reserved_by', 'uid'):
                new[k] = None
            elif lk in ('status',):
                # common values: 'booked', 'reserved', 'available'
                new[k] = 'available'
            else:
                new[k] = unbook_in_json(v)
        return new
    if isinstance(obj, list):
        # If this is a matrix of numbers (e.g., seats as 0/1), set all non-zero to 0
        if obj and all(isinstance(row, list) for row in obj):
            all_numeric_rows = True
            for row in obj:
                if not all(isinstance(x, (int, float)) for x in row):
                    all_numeric_rows = False
                    break
            if all_numeric_rows:
                return [[0 if (isinstance(x, (int, float)) and x != 0) else 0 if x == 0 else x for x in row] for row in obj]
        return [unbook_in_json(x) for x in obj]
    return obj


def reset_seat_maps(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute('SELECT screen_id, seat_map_json FROM scheduled_screens')
    rows = cur.fetchall()
    updated = 0
    for sid, smap in rows:
        if smap is None or smap == '':
            continue
        try:
            data = json.loads(smap)
        except Exception:
            # not valid JSON; skip
            continue
        new_data = unbook_in_json(data)
        new_json = json.dumps(new_data, ensure_ascii=False)
        if new_json != smap:
            cur.execute('UPDATE scheduled_screens SET seat_map_json=? WHERE screen_id=?', (new_json, sid))
            updated += 1
    return updated


def main():
    p = argparse.ArgumentParser(description='Add admin and unbook all seats across scheduled screens; clear bookings.')
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--username', default='snaksartrate')
    p.add_argument('--password', default='pass123')
    p.add_argument('--name', default='Admin')
    p.add_argument('--email', default='admin@example.com')
    p.add_argument('--execute', action='store_true', help='Apply changes; without it, dry-run only')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    db_path = resolve_db(args.db, here)
    if not db_path:
        print('Database file not found.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # counts for preview
        try:
            cur.execute('SELECT COUNT(*) FROM bookings')
            bcount = int(cur.fetchone()[0])
        except sqlite3.Error:
            bcount = 0
        cur.execute('SELECT COUNT(*) FROM scheduled_screens')
        scount = int(cur.fetchone()[0])
        print(f'Database: {db_path}')
        print(f'Bookings to delete (if execute): {bcount}')
        print(f'Scheduled screens to scan for seat maps: {scount}')

        if not args.execute:
            print('\nDry-run only. Will:')
            print(" - Upsert admin user '" + args.username + "'")
            print(' - Delete all rows from bookings (if table exists)')
            print(' - Traverse seat_map_json and mark all seats available')
            print('\nRe-run with --execute to apply.')
            return

        cur.execute('BEGIN;')
        uid = ensure_admin(conn, args.username, args.password, args.name, args.email)
        deleted = clear_bookings(conn)
        updated = reset_seat_maps(conn)
        cur.execute('COMMIT;')
        print(f"Applied. Admin user_id={uid}. Deleted bookings: {deleted}. Updated seat maps: {updated}.")
    except Exception as e:
        try:
            cur.execute('ROLLBACK;')
        except Exception:
            pass
        print(f'Error: {e}')
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
