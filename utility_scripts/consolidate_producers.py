import argparse
import os
import sqlite3
import sys
from typing import List, Tuple, Dict


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
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [r[0] for r in cur.fetchall()]


def table_has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return any((r[1].lower() == col.lower()) for r in cur.fetchall())


def get_producers(conn: sqlite3.Connection) -> List[Tuple[int, str]]:
    cur = conn.cursor()
    # Try common schemas
    for sql in (
        "SELECT producer_id, name FROM producers",
        "SELECT id, name FROM producers",
        "SELECT producer_id, username FROM producers",
        "SELECT id, username FROM producers",
    ):
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            # Ensure first column is int-ish
            if rows and isinstance(rows[0][0], (int,)):
                return [(int(r[0]), str(r[1])) for r in rows]
            else:
                return [(int(r[0]), str(r[1])) for r in rows]
        except sqlite3.Error:
            continue
    return []


def count_updates(conn: sqlite3.Connection, tables: List[str], keep_id: int, other_ids: List[int]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    cur = conn.cursor()
    for t in tables:
        if not table_has_column(conn, t, 'producer_id'):
            continue
        placeholders = ','.join('?' for _ in other_ids)
        if not placeholders:
            continue
        try:
            cur.execute(f"SELECT COUNT(*) FROM \"{t}\" WHERE producer_id IN ({placeholders})", other_ids)
            counts[t] = int(cur.fetchone()[0])
        except sqlite3.Error:
            continue
    return counts


def apply_updates(conn: sqlite3.Connection, tables: List[str], keep_id: int, other_ids: List[int]) -> None:
    cur = conn.cursor()
    placeholders = ','.join('?' for _ in other_ids)
    for t in tables:
        if not table_has_column(conn, t, 'producer_id'):
            continue
        if not placeholders:
            continue
        cur.execute(f"UPDATE \"{t}\" SET producer_id=? WHERE producer_id IN ({placeholders})", [keep_id] + other_ids)


def delete_other_producers(conn: sqlite3.Connection, other_ids: List[int]) -> int:
    if not other_ids:
        return 0
    cur = conn.cursor()
    placeholders = ','.join('?' for _ in other_ids)
    cur.execute(f"DELETE FROM producers WHERE producer_id IN ({placeholders})", other_ids)
    return cur.rowcount


def main():
    p = argparse.ArgumentParser(description='Keep one producer; reassign all references; delete others.')
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--keep-id', type=int, help='producer_id to keep (from producers table)')
    p.add_argument('--execute', action='store_true', help='Apply changes. Without this, performs a dry-run.')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    db_path = resolve_db(args.db, here)
    if not db_path:
        print('Database file not found. Tried relative to CWD and script directory.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('PRAGMA foreign_keys=OFF;')
        producers = get_producers(conn)
        if not producers:
            print('No producers found or unknown producers schema.')
            return
        print('Producers:')
        for pid, name in producers:
            print(f' - {pid}: {name}')

        keep_id = args.keep_id if args.keep_id is not None else producers[0][0]
        if keep_id not in [pid for pid, _ in producers]:
            print(f'Keep id {keep_id} not found among producers.')
            return
        other_ids = [pid for pid, _ in producers if pid != keep_id]
        print(f"\nKeeping producer_id={keep_id}. Deleting others: {other_ids if other_ids else '[]'}")

        tables = list_tables(conn)
        upd_counts = count_updates(conn, tables, keep_id, other_ids)
        print('\nReferences to update (rows with producer_id in others):')
        if upd_counts:
            for t, c in upd_counts.items():
                print(f' - {t}: {c}')
        else:
            print(' <none>')

        if not args.execute:
            print('\nDry-run only. Re-run with --execute and optionally --keep-id <ID> to apply.')
            return

        cur = conn.cursor()
        try:
            cur.execute('BEGIN;')
            apply_updates(conn, tables, keep_id, other_ids)
            deleted = delete_other_producers(conn, other_ids)
            cur.execute('COMMIT;')
        except Exception as e:
            cur.execute('ROLLBACK;')
            print(f'Error applying changes: {e}')
            sys.exit(1)
        finally:
            cur.close()
        print(f'\nApplied. Deleted {deleted} producers. All references now point to {keep_id}.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
