import argparse
import os
import sqlite3
import sys
from typing import List, Set


def list_user_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]


def main():
    p = argparse.ArgumentParser(description="Delete data from all tables except a whitelist.")
    p.add_argument('--db', default='pqr-entertainment/tbms.db', help='Path to SQLite DB')
    p.add_argument('--whitelist', default='movies,theatres,seats', help='Comma-separated table names to KEEP')
    p.add_argument('--execute', action='store_true', help='Actually perform deletions (omit for dry-run)')
    p.add_argument('--reset-seq', action='store_true', help='Reset AUTOINCREMENT sequences (sqlite_sequence)')
    args = p.parse_args()

    # Resolve DB path similarly to inspect_db.py
    requested = args.db
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if os.path.isabs(requested):
        candidates.append(requested)
    else:
        candidates.append(os.path.abspath(requested))
        candidates.append(os.path.join(script_dir, requested))
        candidates.append(os.path.join(script_dir, os.path.basename(requested)))

    db_path = next((p for p in candidates if os.path.exists(p)), None)
    if db_path is None:
        print("Database file not found. Tried:")
        for c in candidates:
            print(f" - {c}")
        sys.exit(1)

    keep: Set[str] = set([t.strip() for t in args.whitelist.split(',') if t.strip()])

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('PRAGMA foreign_keys=OFF;')
        tables = list_user_tables(conn)
        if not tables:
            print('No user tables found.')
            return
        drop_from = [t for t in tables if t not in keep]

        print(f"Database: {db_path}")
        print("All tables:")
        for t in tables:
            print(f" - {t}")
        print("\nWhitelist (kept):")
        for t in sorted(keep):
            print(f" - {t}")
        print("\nWill DELETE FROM these tables:")
        if drop_from:
            for t in drop_from:
                print(f" - {t}")
        else:
            print(" <none>")

        if not args.execute:
            print("\nDry-run only. Re-run with --execute to apply.")
            return

        cur = conn.cursor()
        try:
            cur.execute('BEGIN;')
            for t in drop_from:
                cur.execute(f'DELETE FROM "{t}";')
            if args.reset_seq:
                try:
                    cur.execute('DELETE FROM sqlite_sequence;')
                except sqlite3.Error:
                    pass
            cur.execute('COMMIT;')
        except Exception as e:
            cur.execute('ROLLBACK;')
            print(f"Error during deletion: {e}")
            sys.exit(1)
        finally:
            cur.close()
        print("\nDeletion complete.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
