import argparse
import os
import sqlite3
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
DB = os.path.join(ROOT, 'pqr-entertainment', 'tbms.db')


def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def dedupe_events(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    rows = cur.fetchall() or []
    groups = defaultdict(list)
    for r in rows:
        key = (
            (r['title'] or '').strip().lower(),
            (r['venue'] or '').strip().lower(),
            (r['date'] or '').strip(),
            (r['time'] or '').strip(),
        )
        groups[key].append(r['event_id'])
    actions = []
    for key, ids in groups.items():
        if len(ids) <= 1:
            continue
        ids_sorted = sorted(ids)
        keep = ids_sorted[0]
        dups = ids_sorted[1:]
        actions.append((keep, dups, key))
    return actions


def apply_dedupe_events(conn: sqlite3.Connection, actions):
    cur = conn.cursor()
    for keep, dups, _ in actions:
        qmarks = ','.join('?' for _ in dups)
        cur.execute(f"UPDATE scheduled_screens SET event_id=? WHERE event_id IN ({qmarks})", (keep, *dups))
        cur.execute(f"DELETE FROM events WHERE event_id IN ({qmarks})", tuple(dups))


def dedupe_movie_schedules(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ss.screen_id, ss.theatre_id, ss.movie_id, ss.start_time
        FROM scheduled_screens ss
        WHERE ss.movie_id IS NOT NULL
        """
    )
    rows = cur.fetchall() or []
    groups = defaultdict(list)
    for r in rows:
        key = (int(r['theatre_id']), int(r['movie_id']), (r['start_time'] or '').strip())
        groups[key].append(int(r['screen_id']))
    actions = []
    for key, ids in groups.items():
        if len(ids) <= 1:
            continue
        ids_sorted = sorted(ids)
        keep = ids_sorted[0]
        dups = ids_sorted[1:]
        actions.append((keep, dups, key))
    return actions


def apply_dedupe_movie_schedules(conn: sqlite3.Connection, actions):
    cur = conn.cursor()
    for keep, dups, _ in actions:
        if not dups:
            continue
        qmarks = ','.join('?' for _ in dups)
        # Reassign bookings (if any) to the kept screen
        try:
            cur.execute(f"UPDATE bookings SET screen_id=? WHERE screen_id IN ({qmarks})", (keep, *dups))
        except sqlite3.Error:
            pass
        cur.execute(f"DELETE FROM scheduled_screens WHERE screen_id IN ({qmarks})", tuple(dups))


def main():
    p = argparse.ArgumentParser(description='Deduplicate events and movie schedules keeping the lowest ID when name/location/timing are identical.')
    p.add_argument('--db', default=DB)
    p.add_argument('--execute', action='store_true', help='Apply changes; otherwise dry-run')
    args = p.parse_args()

    conn = connect(args.db)
    try:
        ev_actions = dedupe_events(conn)
        ss_actions = dedupe_movie_schedules(conn)

        print('Events duplicates to remove:', len(ev_actions))
        for keep, dups, key in ev_actions[:20]:
            print('  keep', keep, 'delete', dups, 'key=', key)
        if len(ev_actions) > 20:
            print('  ... and', len(ev_actions)-20, 'more')

        print('Movie schedule duplicates to remove:', len(ss_actions))
        for keep, dups, key in ss_actions[:20]:
            print('  keep', keep, 'delete', dups, 'key=', key)
        if len(ss_actions) > 20:
            print('  ... and', len(ss_actions)-20, 'more')

        if not args.execute:
            print('\nDry-run only. Re-run with --execute to apply.')
            return

        cur = conn.cursor()
        cur.execute('BEGIN;')
        apply_dedupe_events(conn, ev_actions)
        apply_dedupe_movie_schedules(conn, ss_actions)
        cur.execute('COMMIT;')
        print('Applied.')
    except Exception as e:
        try:
            conn.execute('ROLLBACK;')
        except Exception:
            pass
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
