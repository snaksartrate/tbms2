import sqlite3, os, json
p = os.path.join(os.path.dirname(__file__), 'tbms.db')
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute("SELECT screen_id, substr(seat_map_json,1,2000) FROM scheduled_screens WHERE seat_map_json IS NOT NULL AND seat_map_json<>'' LIMIT 5")
rows = cur.fetchall()
for sid, smap in rows:
    print(f"\nSCREEN {sid}:")
    try:
        data = json.loads(smap)
        def walk(x, depth=0):
            if depth>2:
                return '...'
            if isinstance(x, dict):
                return {k: walk(v, depth+1) for k,v in list(x.items())[:8]}
            if isinstance(x, list):
                return [walk(v, depth+1) for v in x[:8]]
            return x
        print('type:', type(data).__name__)
        print('shape:', walk(data))
        # try to find seat objects by scanning for dicts with boolean fields
        def collect_flags(x, out):
            if isinstance(x, dict):
                for k,v in x.items():
                    if isinstance(v, (bool, str)):
                        out[k] = out.get(k,0)+1
                    collect_flags(v, out)
            elif isinstance(x, list):
                for v in x:
                    collect_flags(v, out)
        flags = {}
        collect_flags(data, flags)
        print('common keys:', sorted(list(flags.keys()))[:20])
    except Exception as e:
        print('invalid json:', str(e))
        print('raw:', smap[:200])
conn.close()
