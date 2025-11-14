import argparse
import os
import sqlite3
import sys


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


def main():
    p = argparse.ArgumentParser(description="Delete all users with role='producer' except a keeper username.")
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--keep-username', default='producer_master')
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    db_path = resolve_db(args.db, here)
    if not db_path:
        print('Database file not found.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE role='producer'")
        rows = cur.fetchall()
        to_delete = [(uid, uname) for uid, uname in rows if uname != args.keep_username]
        print(f"Found {len(rows)} producer users. Will delete {len(to_delete)} (keeping username='{args.keep_username}').")
        if to_delete:
            print('To delete:')
            for uid, uname in to_delete:
                print(f' - {uid}: {uname}')
        if not args.execute:
            print('\nDry-run only. Re-run with --execute to apply.')
            return
        cur.execute('BEGIN;')
        ids = [uid for uid, _ in to_delete]
        if ids:
            qmarks = ','.join('?' for _ in ids)
            cur.execute(f"DELETE FROM users WHERE user_id IN ({qmarks})", ids)
        cur.execute('COMMIT;')
        print('Deletion complete.')
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
