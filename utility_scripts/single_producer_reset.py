import argparse
import os
import sqlite3
import sys
from typing import Optional


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


def get_or_create_user(conn: sqlite3.Connection, username: str, password: str, name: str, email: str) -> int:
    cur = conn.cursor()
    # users schema: (user_id, username, password, role, name, email, balance)
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur.execute(
        "INSERT INTO users (username, password, role, name, email, balance) VALUES (?,?,?,?,?,0)",
        (username, password, 'producer', name, email),
    )
    return int(cur.lastrowid)


def create_producer(conn: sqlite3.Connection, user_id: int, name: str, details: str = '') -> int:
    cur = conn.cursor()
    # producers schema: (producer_id, user_id, name, details)
    cur.execute(
        "INSERT INTO producers (user_id, name, details) VALUES (?,?,?)",
        (user_id, name, details),
    )
    return int(cur.lastrowid)


def count_table(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM \"{table}\";")
    return int(cur.fetchone()[0])


def main():
    p = argparse.ArgumentParser(description='Ensure exactly one producer exists, link all movies to it, delete others.')
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--username', default='producer_master')
    p.add_argument('--password', default='pass123')
    p.add_argument('--name', default='Master Producer')
    p.add_argument('--email', default='producer_master@example.com')
    p.add_argument('--details', default='Single canonical producer')
    p.add_argument('--execute', action='store_true', help='Apply changes (default is dry-run)')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    db_path = resolve_db(args.db, here)
    if not db_path:
        print('Database file not found.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('PRAGMA foreign_keys=OFF;')
        cur = conn.cursor()

        # Inspect current counts
        try:
            cur.execute('SELECT producer_id, user_id, name FROM producers')
            producers = cur.fetchall()
        except sqlite3.Error as e:
            print(f'Error reading producers: {e}')
            return
        movie_count = count_table(conn, 'movies')
        print(f'Database: {db_path}')
        print(f'Current producers: {len(producers)}')
        print(f'Movies to relink: {movie_count}')

        if not args.execute:
            print('\nDry-run only. Will:')
            print(' - Create user (if missing) with role=producer')
            print(' - Create one producer referencing that user')
            print(' - Update all movies to use that producer_id')
            print(' - Delete all other producers')
            print("\nRe-run with --execute to apply.")
            return

        try:
            cur.execute('BEGIN;')
            user_id = get_or_create_user(conn, args.username, args.password, args.name, args.email)
            # Ensure a producer for this user; if exists, reuse, else create
            cur.execute('SELECT producer_id FROM producers WHERE user_id=?', (user_id,))
            row = cur.fetchone()
            if row:
                new_producer_id = int(row[0])
            else:
                new_producer_id = create_producer(conn, user_id, args.name, args.details)

            # Update movies to point to new_producer_id
            cur.execute('UPDATE movies SET producer_id=?', (new_producer_id,))

            # Delete all other producers
            cur.execute('DELETE FROM producers WHERE producer_id <> ?', (new_producer_id,))

            cur.execute('COMMIT;')
        except Exception as e:
            cur.execute('ROLLBACK;')
            print(f'Error applying changes: {e}')
            sys.exit(1)
        finally:
            cur.close()
        print('Applied. Exactly one producer remains and all movies reference it.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
