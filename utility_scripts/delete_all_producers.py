import argparse
import os
import sqlite3
import sys
from typing import List


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


def list_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]


def table_has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return any((r[1].lower() == col.lower()) for r in cur.fetchall())


def main():
    p = argparse.ArgumentParser(description='Delete ALL producers, nulling producer_id in referencing tables first.')
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--execute', action='store_true', help='Apply changes. Without this, performs a dry-run.')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    db_path = resolve_db(args.db, here)
    if not db_path:
        print('Database file not found.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('PRAGMA foreign_keys=OFF;')
        tables = list_tables(conn)
        ref_tables = [t for t in tables if table_has_column(conn, t, 'producer_id') and t != 'producers']

        # Counts
        cur = conn.cursor()
        total_updates = {}
        for t in ref_tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}" WHERE producer_id IS NOT NULL;')
                total_updates[t] = int(cur.fetchone()[0])
            except sqlite3.Error:
                total_updates[t] = 0
        try:
            cur.execute('SELECT COUNT(*) FROM producers;')
            prod_count = int(cur.fetchone()[0])
        except sqlite3.Error:
            prod_count = 0

        print(f'Database: {db_path}')
        print('Tables with producer_id to null:')
        if ref_tables:
            for t in ref_tables:
                print(f' - {t}: {total_updates.get(t,0)} rows to update')
        else:
            print(' <none>')
        print(f'Producers to delete: {prod_count}')

        if not args.execute:
            print('\nDry-run only. Re-run with --execute to apply.')
            return

        try:
            cur.execute('BEGIN;')
            # Null out references first
            for t in ref_tables:
                cur.execute(f'UPDATE "{t}" SET producer_id = NULL WHERE producer_id IS NOT NULL;')
            # Delete all producers
            cur.execute('DELETE FROM producers;')
            cur.execute('COMMIT;')
        except Exception as e:
            cur.execute('ROLLBACK;')
            print(f'Error applying changes: {e}')
            sys.exit(1)
        finally:
            cur.close()
        print('Deletion complete. All producers removed and references nulled.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
