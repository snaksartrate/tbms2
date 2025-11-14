import argparse
import sqlite3
import sys
import os
from typing import List, Tuple


def get_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]


def get_columns(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str, int]]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = []
    for cid, name, ctype, notnull, dflt_value, pk in cur.fetchall():
        cols.append((name, ctype or '', pk))
    return cols


def get_row_count(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM \"{table}\";")
    return cur.fetchone()[0]


def fetch_rows(conn: sqlite3.Connection, table: str, limit: int = None) -> List[Tuple]:
    cur = conn.cursor()
    if limit is not None:
        cur.execute(f"SELECT * FROM \"{table}\" LIMIT {int(limit)};")
    else:
        cur.execute(f"SELECT * FROM \"{table}\";")
    return cur.fetchall()


def format_row(values: List, widths: List[int]) -> str:
    cells = []
    for v, w in zip(values, widths):
        s = '' if v is None else str(v)
        if len(s) > w:
            s = s[: max(0, w - 1)] + '…'
        cells.append(s.ljust(w))
    return " | ".join(cells)


def compute_widths(headers: List[str], rows: List[Tuple], max_col_width: int) -> List[int]:
    widths = [min(max_col_width, len(h)) for h in headers]
    for row in rows:
        for i, v in enumerate(row):
            l = 0 if v is None else len(str(v))
            if l > widths[i]:
                widths[i] = min(max_col_width, l)
    return widths


def print_table(conn: sqlite3.Connection, table: str, limit: int, max_col_width: int):
    cols = get_columns(conn, table)
    headers = [c[0] for c in cols]
    types = [c[1] for c in cols]
    pk = [c[2] for c in cols]

    count = get_row_count(conn, table)
    rows = fetch_rows(conn, table, None if limit == 0 else limit)

    widths = compute_widths(headers, rows, max_col_width)

    print(f"\n=== {table} ===")
    meta = []
    if any(types):
        meta.append("types: " + ", ".join(types))
    if any(pk):
        pk_cols = [headers[i] for i, v in enumerate(pk) if v]
        if pk_cols:
            meta.append("pk: " + ", ".join(pk_cols))
    if meta:
        print("(" + " | ".join(meta) + ")")
    print(f"rows: {count}")

    if not headers:
        print("<no columns>")
        return

    sep = "-+-".join('-' * w for w in widths)
    print(format_row(headers, widths))
    print(sep)
    for r in rows:
        print(format_row(list(r), widths))

    if limit and count > limit:
        print(f"... {count - limit} more rows not shown. Use --limit 0 to show all.")


def print_query(conn: sqlite3.Connection, title: str, query: str, params: tuple = (), max_col_width: int = 60, limit: int = 0):
    cur = conn.cursor()
    q = query
    if limit and limit > 0:
        q = f"{query} LIMIT {int(limit)}"
    cur.execute(q, params)
    rows = cur.fetchall()
    if not rows:
        return
    headers = [d[0] for d in cur.description]
    widths = compute_widths(headers, rows, max_col_width)
    print(f"\n=== {title} ===")
    sep = "-+-".join('-' * w for w in widths)
    print(format_row(headers, widths))
    print(sep)
    for r in rows:
        print(format_row(list(r), widths))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='pqr-entertainment/tbms.db')
    p.add_argument('--max-col-width', type=int, default=60)
    args = p.parse_args()

    # Resolve DB path robustly: try CWD, then script dir, then script dir + basename
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
        print("Failed to open database: file not found. Tried:")
        for pth in candidates:
            print(f" - {pth}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(f"Failed to open database: {e}")
        sys.exit(1)

    try:
        while True:
            print("\n-------- MENU --------")
            print("1. Show users")
            print("2. Show producers")
            print("3. Show admins")
            print("4. Show city")
            print("5. Show theatre")
            print("6. Show film")
            print("7. Show schedule")
            print("-1. Exit")
            try:
                choice = int(input("Enter option number: ").strip())
            except Exception:
                print("Invalid input. Enter a number.")
                continue

            if choice == -1:
                break
            elif choice == 1:
                # show only end-users, not producers/admins
                print_query(conn, "users", "SELECT * FROM users WHERE role = 'user'", max_col_width=args.max_col_width, limit=0)
            elif choice == 2:
                print_query(conn, "producers", "SELECT * FROM producers", max_col_width=args.max_col_width, limit=0)
            elif choice == 3:
                # admins are employees with designation='admin'
                print_query(conn, "admins", "SELECT * FROM employees WHERE designation = 'admin'", max_col_width=args.max_col_width, limit=0)
            elif choice == 4:
                # show distinct cities from theatres
                print_query(conn, "city", "SELECT DISTINCT city FROM theatres", max_col_width=args.max_col_width, limit=0)
            elif choice == 5:
                print_query(conn, "theatre", "SELECT * FROM theatres", max_col_width=args.max_col_width, limit=0)
            elif choice == 6:
                print_query(conn, "film", "SELECT * FROM movies", max_col_width=args.max_col_width, limit=0)
            elif choice == 7:
                print_query(conn, "schedule", "SELECT * FROM scheduled_screens", max_col_width=args.max_col_width, limit=0)
            else:
                print("Unknown option.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
