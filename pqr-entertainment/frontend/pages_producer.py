import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json
from dbwrap import db

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except Exception:
    FigureCanvasTkAgg = None
    plt = None

def show_producer_analytics(app):
    """Analytics for the logged-in producer (movies + events)"""
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)

    producer_id = app.get_current_producer_id()
    if not producer_id:
        messagebox.showerror("Error", "Producer profile not found.")
        return

    if not FigureCanvasTkAgg or not plt:
        frame = tk.Frame(app.main_container, bg='#1a1a1a')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(frame, text="Matplotlib not available. Please install matplotlib to view analytics.",
                 bg='#1a1a1a', fg='white', font=('Arial', 14)).pack(pady=20)
        return

    content = tk.Frame(app.main_container, bg='#1a1a1a')
    content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # KPIs
    movies_count = db.execute_query("SELECT COUNT(*) as c FROM movies WHERE producer_id = ?", (producer_id,), fetch_one=True)['c']
    events_count = db.execute_query("SELECT COUNT(*) as c FROM events WHERE host_id = ?", (producer_id,), fetch_one=True)['c']
    screens_count = db.execute_query(
        """
        SELECT COUNT(*) as c FROM scheduled_screens
        WHERE (movie_id IN (SELECT movie_id FROM movies WHERE producer_id = ?))
           OR (event_id IN (SELECT event_id FROM events WHERE host_id = ?))
        """, (producer_id, producer_id), fetch_one=True)['c']
    agg = db.execute_query(
        """
        SELECT SUM(b.amount) as revenue, COUNT(b.booking_id) as bookings
        FROM bookings b
        JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
        WHERE (ss.movie_id IN (SELECT movie_id FROM movies WHERE producer_id = ?))
           OR (ss.event_id IN (SELECT event_id FROM events WHERE host_id = ?))
        """, (producer_id, producer_id), fetch_one=True)
    total_revenue = agg['revenue'] or 0
    total_bookings = agg['bookings'] or 0

    # Avg rating
    m_avg = db.execute_query("SELECT AVG(average_rating) as a, COUNT(*) as c FROM movies WHERE producer_id = ?", (producer_id,), fetch_one=True)
    e_avg = db.execute_query("SELECT AVG(average_rating) as a, COUNT(*) as c FROM events WHERE host_id = ?", (producer_id,), fetch_one=True)
    avg_rating = 0
    total_titles = (m_avg['c'] or 0) + (e_avg['c'] or 0)
    if total_titles:
        m_part = (m_avg['a'] or 0) * (m_avg['c'] or 0)
        e_part = (e_avg['a'] or 0) * (e_avg['c'] or 0)
        avg_rating = (m_part + e_part) / total_titles if total_titles else 0

    kpi = tk.Frame(content, bg='#1a1a1a')
    kpi.pack(fill=tk.X)
    items = [
        ("🎬 Movies", movies_count),
        ("🎭 Events", events_count),
        ("🗓️ Screens", screens_count),
        ("🎫 Bookings", total_bookings),
        ("💰 Revenue", f"₹{int(total_revenue)}"),
        ("⭐ Avg Rating", f"{avg_rating:.1f}/5.0"),
    ]
    for i, (label, val) in enumerate(items):
        card = tk.Frame(kpi, bg='#2a2a2a', width=180, height=80)
        card.pack_propagate(False)
        card.pack(side=tk.LEFT, padx=8, pady=10)
        tk.Label(card, text=label, bg='#2a2a2a', fg='#bbb', font=('Arial', 10)).pack()
        tk.Label(card, text=str(val), bg='#2a2a2a', fg='white', font=('Arial', 16, 'bold')).pack()

    # Data for charts
    sales_movies = db.execute_query(
        """
        SELECT m.title as title, SUM(b.amount) AS total
        FROM bookings b
        JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
        JOIN movies m ON ss.movie_id = m.movie_id
        WHERE m.producer_id = ?
        GROUP BY m.title
        """, (producer_id,), fetch_all=True)
    sales_events = db.execute_query(
        """
        SELECT e.title as title, SUM(b.amount) AS total
        FROM bookings b
        JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
        JOIN events e ON ss.event_id = e.event_id
        WHERE e.host_id = ?
        GROUP BY e.title
        """, (producer_id,), fetch_all=True)
    sales = {}
    for row in (sales_movies or []):
        sales[row['title']] = sales.get(row['title'], 0) + (row['total'] or 0)
    for row in (sales_events or []):
        sales[row['title']] = sales.get(row['title'], 0) + (row['total'] or 0)

    trends = db.execute_query(
        """
        SELECT DATE(b.booking_date) as d, COUNT(*) as c
        FROM bookings b
        JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
        WHERE DATE(b.booking_date) >= DATE('now', '-14 day')
          AND ((ss.movie_id IN (SELECT movie_id FROM movies WHERE producer_id = ?))
            OR (ss.event_id IN (SELECT event_id FROM events WHERE host_id = ?)))
        GROUP BY DATE(b.booking_date)
        ORDER BY d
        """, (producer_id, producer_id), fetch_all=True)

    genre_counts = {}
    for r in (db.execute_query("SELECT genres_json FROM movies WHERE producer_id = ?", (producer_id,), fetch_all=True) or []):
        try:
            for g in json.loads(r['genres_json'] or '[]'):
                genre_counts[g] = genre_counts.get(g, 0) + 1
        except Exception:
            pass
    for r in (db.execute_query("SELECT genres_json FROM events WHERE host_id = ?", (producer_id,), fetch_all=True) or []):
        try:
            for g in json.loads(r['genres_json'] or '[]'):
                genre_counts[g] = genre_counts.get(g, 0) + 1
        except Exception:
            pass

    screens = db.execute_query(
        """
        SELECT seat_map_json FROM scheduled_screens
        WHERE DATE(start_time) >= DATE('now') AND DATE(start_time) <= DATE('now', '+3 day')
          AND ((movie_id IN (SELECT movie_id FROM movies WHERE producer_id = ?))
            OR (event_id IN (SELECT event_id FROM events WHERE host_id = ?)))
        """, (producer_id, producer_id), fetch_all=True)
    total_seats = len(screens) * 100
    booked = 0
    for s in (screens or []):
        try:
            seat_map = json.loads(s['seat_map_json'])
            booked += sum(row.count(1) for row in seat_map)
        except Exception:
            pass
    occupancy = (booked / total_seats) * 100 if total_seats else 0

    top = tk.Frame(content, bg='#1a1a1a')
    bottom = tk.Frame(content, bg='#1a1a1a')
    top.pack(fill=tk.BOTH, expand=True)
    bottom.pack(fill=tk.BOTH, expand=True)

    def add_chart(parent, fig):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    fig1, ax1 = plt.subplots(figsize=(5,3))
    if sales:
        items = sorted(sales.items(), key=lambda x: x[1], reverse=True)[:10]
        titles = [k for k, _ in items]
        totals = [v for _, v in items]
        ax1.bar(titles, totals, color='#4CAF50')
        ax1.set_title('Sales per Title')
        ax1.tick_params(axis='x', labelrotation=45)
    else:
        ax1.text(0.5,0.5,'No data', ha='center')
    add_chart(top, fig1)

    fig2, ax2 = plt.subplots(figsize=(5,3))
    if trends:
        days = [row['d'] for row in trends]
        counts = [row['c'] for row in trends]
        ax2.plot(days, counts, marker='o', color='#2196F3')
        ax2.set_title('Bookings (Last 14 days)')
        ax2.tick_params(axis='x', labelrotation=45)
    else:
        ax2.text(0.5,0.5,'No data', ha='center')
    add_chart(top, fig2)

    fig3, ax3 = plt.subplots(figsize=(5,3))
    if genre_counts:
        labels = list(genre_counts.keys())
        sizes = list(genre_counts.values())
        wedges, _ = ax3.pie(sizes, wedgeprops=dict(width=0.4))
        ax3.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0.5))
        ax3.set_title('Genre Distribution')
    else:
        ax3.text(0.5,0.5,'No data', ha='center')
    add_chart(bottom, fig3)

    fig4, ax4 = plt.subplots(figsize=(5,3), subplot_kw=dict(aspect="equal"))
    occupied = max(0, min(100, occupancy))
    free = 100 - occupied
    ax4.pie([occupied, free], startangle=180, counterclock=False, colors=['#FF9800', '#EEEEEE'], wedgeprops=dict(width=0.4))
    ax4.set_title(f'Avg Occupancy: {occupied:.1f}%')
    ax4.set_ylim(-1, 0.1)
    add_chart(bottom, fig4)

def show_producer_dashboard(app):
    """Producer dashboard: movies and events grids with filters and CRUD"""
    import tkinter as tk
    from tkinter import ttk
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_search=False, show_username=True)

    producer_id = app.get_current_producer_id()
    if not producer_id:
        messagebox.showerror("Error", "Producer profile not found for this account.")
        return

    content_frame = tk.Frame(app.main_container, bg='#1a1a1a')
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    header_row = tk.Frame(content_frame, bg='#1a1a1a')
    header_row.pack(fill=tk.X)
    tk.Label(header_row, text="My Movies", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    tk.Button(header_row, text="➕ Add Movie", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=lambda: app.open_movie_form()).pack(side=tk.RIGHT)

    filter_row = tk.Frame(content_frame, bg='#1a1a1a')
    filter_row.pack(fill=tk.X, pady=10)
    tk.Label(filter_row, text="Title:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    title_var = tk.StringVar(); tk.Entry(filter_row, textvariable=title_var, width=25).pack(side=tk.LEFT, padx=5)
    tk.Label(filter_row, text="Genre:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(15,0))
    genre_var = tk.StringVar(value='All'); ttk.Combobox(filter_row, textvariable=genre_var, values=['All'] + app.get_all_genres(), width=18, state='readonly').pack(side=tk.LEFT, padx=5)
    tk.Label(filter_row, text="Language:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(15,0))
    lang_var = tk.StringVar(value='All'); ttk.Combobox(filter_row, textvariable=lang_var, values=['All'] + app.get_all_languages(), width=18, state='readonly').pack(side=tk.LEFT, padx=5)

    # Scrollable container for Movies grid
    movies_canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
    movies_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=movies_canvas.yview)
    grid_container = tk.Frame(movies_canvas, bg='#1a1a1a')
    grid_container.bind("<Configure>", lambda e: movies_canvas.configure(scrollregion=movies_canvas.bbox("all")))
    movies_canvas.create_window((0, 0), window=grid_container, anchor="nw")
    movies_canvas.configure(yscrollcommand=movies_scrollbar.set)

    def load_grid():
        for w in grid_container.winfo_children(): w.destroy()
        query = "SELECT * FROM movies WHERE producer_id = ?"
        params = [producer_id]
        if title_var.get():
            query += " AND title LIKE ?"; params.append(f"%{title_var.get()}%")
        movies = db.execute_query(query, tuple(params), fetch_all=True)
        sel_genre = genre_var.get(); sel_lang = lang_var.get(); filtered = []
        for m in (movies or []):
            try:
                genres = json.loads(m.get('genres_json') or '[]')
            except Exception:
                genres = []
            try:
                languages = json.loads(m.get('languages_json') or '[]')
            except Exception:
                languages = []
            if sel_genre != 'All' and sel_genre not in genres: continue
            if sel_lang != 'All' and sel_lang not in languages: continue
            filtered.append(m)

        # Deduplicate by movie_id (fallback to title)
        movies_unique = []
        seen = set()
        for m in filtered:
            key = m.get('movie_id') if isinstance(m, dict) else m.get('title')
            if key in seen:
                continue
            seen.add(key)
            movies_unique.append(m)
        grid = tk.Frame(grid_container, bg='#1a1a1a'); grid.pack(fill=tk.BOTH, expand=True)
        for idx, movie in enumerate(movies_unique):
            r, c = divmod(idx, 3)
            card = tk.Frame(grid, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            card.grid(row=r, column=c, padx=10, pady=10, sticky='nsew')
            img_frame = tk.Frame(card, bg='#444', width=160, height=120); img_frame.pack(padx=10, pady=10); img_frame.pack_propagate(False)
            tk.Label(img_frame, text="🎞️", font=('Arial', 28), bg='#444', fg='white').pack(expand=True)
            tk.Label(card, text=movie['title'], font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white', wraplength=180).pack()
            tk.Label(card, text=f"⭐ {movie.get('average_rating', 0)}/5.0", font=('Arial', 10), bg='#2a2a2a', fg='#FFD700').pack()
            # Genres
            try:
                g = json.loads(movie.get('genres_json') or '[]')
                if g:
                    tk.Label(card, text=', '.join(g[:2]), font=('Arial', 9), bg='#2a2a2a', fg='#bbb').pack()
            except Exception:
                pass
            btns = tk.Frame(card, bg='#2a2a2a'); btns.pack(pady=8)
            tk.Button(btns, text="Edit", bg='#2196F3', fg='white', width=8, command=lambda m=movie: app.open_movie_form(edit=True, movie=m)).pack(side=tk.LEFT, padx=5)
            tk.Button(btns, text="Delete", bg='#d32f2f', fg='white', width=8, command=lambda mid=movie['movie_id']: app.delete_movie(mid)).pack(side=tk.LEFT, padx=5)
        for i in range(3): grid.grid_columnconfigure(i, weight=1)

    # Pack movies scrollable after filters
    movies_canvas.pack(side="left", fill="both", expand=True)
    movies_scrollbar.pack(side="right", fill="y")

    action_row = tk.Frame(content_frame, bg='#1a1a1a'); action_row.pack(fill=tk.X, pady=5)
    tk.Button(action_row, text="Apply Filters", bg='#4CAF50', fg='white', command=load_grid).pack(side=tk.LEFT)
    tk.Button(action_row, text="Clear", bg='#555', fg='white', command=lambda: [title_var.set(''), genre_var.set('All'), lang_var.set('All'), load_grid()]).pack(side=tk.LEFT, padx=8)
    load_grid()

    # Events section
    sep = tk.Frame(content_frame, bg='#1a1a1a', height=10); sep.pack(fill=tk.X)
    header_row2 = tk.Frame(content_frame, bg='#1a1a1a'); header_row2.pack(fill=tk.X, pady=(10,0))
    tk.Label(header_row2, text="My Events", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    tk.Button(header_row2, text="➕ Add Event", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=lambda: app.open_event_form()).pack(side=tk.RIGHT)
    evt_filter = tk.Frame(content_frame, bg='#1a1a1a'); evt_filter.pack(fill=tk.X, pady=8)
    tk.Label(evt_filter, text="Title:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    evt_title_var = tk.StringVar(); tk.Entry(evt_filter, textvariable=evt_title_var, width=25).pack(side=tk.LEFT, padx=5)
    # Event genre filter
    tk.Label(evt_filter, text="Genre:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(15,0))
    try:
        all_evt_genres = sorted({g for row in db.execute_query("SELECT genres_json FROM events", fetch_all=True) for g in json.loads((row.get('genres_json') or '[]'))})
    except Exception:
        all_evt_genres = []
    evt_genre_var = tk.StringVar(value='All'); ttk.Combobox(evt_filter, textvariable=evt_genre_var, values=['All'] + all_evt_genres, width=18, state='readonly').pack(side=tk.LEFT, padx=5)

    # Scrollable container for Events grid
    evt_canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
    evt_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=evt_canvas.yview)
    evt_grid_container = tk.Frame(evt_canvas, bg='#1a1a1a'); evt_grid_container.bind("<Configure>", lambda e: evt_canvas.configure(scrollregion=evt_canvas.bbox("all")))
    evt_canvas.create_window((0, 0), window=evt_grid_container, anchor="nw")
    evt_canvas.configure(yscrollcommand=evt_scrollbar.set)

    def load_events():
        for w in evt_grid_container.winfo_children(): w.destroy()
        q = "SELECT * FROM events WHERE host_id = ?"; ps = [producer_id]
        if evt_title_var.get(): q += " AND title LIKE ?"; ps.append(f"%{evt_title_var.get()}%")
        events = db.execute_query(q, tuple(ps), fetch_all=True)
        # Apply genre filter
        filtered_events = []
        for ev in (events or []):
            try:
                g = json.loads(ev.get('genres_json') or '[]')
            except Exception:
                g = []
            if evt_genre_var.get() != 'All' and evt_genre_var.get() not in g:
                continue
            filtered_events.append(ev)

        # Deduplicate by event_id (fallback to title)
        events_unique = []
        seen_e = set()
        for ev in filtered_events:
            key = ev.get('event_id') if isinstance(ev, dict) else ev.get('title')
            if key in seen_e:
                continue
            seen_e.add(key)
            events_unique.append(ev)

        grid = tk.Frame(evt_grid_container, bg='#1a1a1a'); grid.pack(fill=tk.BOTH, expand=True)
        for idx, ev in enumerate(events_unique):
            r, c = divmod(idx, 3)
            card = tk.Frame(grid, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            card.grid(row=r, column=c, padx=10, pady=10, sticky='nsew')
            img_frame = tk.Frame(card, bg='#444', width=160, height=120); img_frame.pack(padx=10, pady=10); img_frame.pack_propagate(False)
            tk.Label(img_frame, text="🎭", font=('Arial', 28), bg='#444', fg='white').pack(expand=True)
            tk.Label(card, text=ev['title'], font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white', wraplength=180).pack()
            tk.Label(card, text=f"⭐ {ev.get('average_rating', 0)}/5.0", font=('Arial', 10), bg='#2a2a2a', fg='#FFD700').pack()
            # Genres
            try:
                g = json.loads(ev.get('genres_json') or '[]')
                if g:
                    tk.Label(card, text=', '.join(g[:2]), font=('Arial', 9), bg='#2a2a2a', fg='#bbb').pack()
            except Exception:
                pass
            btns = tk.Frame(card, bg='#2a2a2a'); btns.pack(pady=8)
            tk.Button(btns, text="Edit", bg='#2196F3', fg='white', width=8, command=lambda e=ev: app.open_event_form(edit=True, event=e)).pack(side=tk.LEFT, padx=5)
            tk.Button(btns, text="Delete", bg='#d32f2f', fg='white', width=8, command=lambda eid=ev['event_id']: app.delete_event(eid)).pack(side=tk.LEFT, padx=5)
        for i in range(3): grid.grid_columnconfigure(i, weight=1)

    tk.Button(evt_filter, text="Apply", bg='#4CAF50', fg='white', command=load_events).pack(side=tk.LEFT, padx=8)
    tk.Button(evt_filter, text="Clear", bg='#555', fg='white', command=lambda: [evt_title_var.set(''), load_events()]).pack(side=tk.LEFT)
    load_events()

    # Pack events scrollable
    evt_canvas.pack(side="left", fill="both", expand=True)
    evt_scrollbar.pack(side="right", fill="y")

def open_movie_form(app, edit=False, movie=None):
    return app.open_movie_form(edit=edit, movie=movie)

def open_event_form(app, edit=False, event=None):
    return app.open_event_form(edit=edit, event=event)

def delete_movie(app, movie_id: int):
    return app.delete_movie(movie_id)

def delete_event(app, event_id: int):
    return app.delete_event(event_id)
