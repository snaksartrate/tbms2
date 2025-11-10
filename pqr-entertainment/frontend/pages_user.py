import tkinter as tk
from tkinter import ttk
from dbwrap import db
import json
from datetime import datetime

def show_events_page(app):
    """Full events listing page (delegated from main)"""
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_search=True, show_username=True)
    content_frame = tk.Frame(app.main_container, bg='#1a1a1a')
    content_frame.pack(fill=tk.BOTH, expand=True)
    tk.Label(content_frame, text="Discover Events", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(anchor='w', padx=20, pady=(10,6))

    # Filters
    filter_row = tk.Frame(content_frame, bg='#1a1a1a'); filter_row.pack(fill=tk.X, padx=20, pady=(0,10))
    tk.Label(filter_row, text="Title:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    title_var = tk.StringVar(); tk.Entry(filter_row, textvariable=title_var, width=30).pack(side=tk.LEFT, padx=6)
    tk.Label(filter_row, text="Genre:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(12,0))
    try:
        all_evt_genres = sorted({g for row in db.execute_query("SELECT genres_json FROM events", fetch_all=True) for g in json.loads((row.get('genres_json') or '[]'))})
    except Exception:
        all_evt_genres = []
    genre_var = tk.StringVar(value='All'); ttk.Combobox(filter_row, textvariable=genre_var, values=['All'] + all_evt_genres, width=18, state='readonly').pack(side=tk.LEFT, padx=6)

    # Scrollable grid
    canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scrollable = tk.Frame(canvas, bg='#1a1a1a')
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def load_events():
        for w in scrollable.winfo_children(): w.destroy()
        q = "SELECT * FROM events"
        ps = []
        if title_var.get():
            q += " WHERE title LIKE ?"; ps.append(f"%{title_var.get()}%")
        q += " ORDER BY upload_date DESC"
        events = db.execute_query(q, tuple(ps) if ps else None, fetch_all=True)
        # apply genre filter
        filtered = []
        for e in (events or []):
            try:
                genres = json.loads(e.get('genres_json') or '[]')
            except Exception:
                genres = []
            if genre_var.get() != 'All' and genre_var.get() not in genres:
                continue
            filtered.append(e)
        app.create_event_grid(scrollable, filtered)

    action_row = tk.Frame(content_frame, bg='#1a1a1a'); action_row.pack(fill=tk.X, padx=20, pady=(0,10))
    tk.Button(action_row, text="Apply", bg='#4CAF50', fg='white', command=load_events).pack(side=tk.LEFT)
    tk.Button(action_row, text="Clear", bg='#555', fg='white', command=lambda: [title_var.set(''), genre_var.set('All'), load_events()]).pack(side=tk.LEFT, padx=8)

    load_events()
    canvas.pack(side="left", fill="both", expand=True, padx=20)
    scrollbar.pack(side="right", fill="y")

def show_user_home(app):
    """User homepage with featured banner, movies grid, testimonials, footer"""
    import json
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_search=True, show_username=True)

    canvas = tk.Canvas(app.main_container, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(app.main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    banner_frame = tk.Frame(scrollable_frame, bg='#2a2a2a')
    banner_frame.pack(fill=tk.X, padx=20, pady=20)
    tk.Label(banner_frame, text="🎬 Browse Movies & Events", font=('Arial', 24, 'bold'), bg='#2a2a2a', fg='white').pack(pady=10)
    cards_frame = tk.Frame(banner_frame, bg='#2a2a2a'); cards_frame.pack(fill=tk.X, padx=10, pady=10)
    featured = db.execute_query("SELECT * FROM movies ORDER BY average_rating DESC LIMIT 6", fetch_all=True)
    app._featured_idx_left = 0; app._featured_idx_right = 1
    def render_featured_card(parent, movie):
        card = tk.Frame(parent, bg='#333', width=260, height=160); card.pack_propagate(False)
        title = movie['title'][:28] + ('…' if len(movie['title']) > 28 else '')
        tk.Label(card, text=title, font=('Arial', 12, 'bold'), bg='#333', fg='white').pack(pady=10)
        tk.Label(card, text=f"⭐ {movie['average_rating']}/5.0", font=('Arial', 10), bg='#333', fg='#FFD700').pack()
        tk.Button(card, text="Open", bg='#4CAF50', fg='white', font=('Arial', 10), command=lambda m=movie: app.show_movie_detail(m)).pack(pady=8)
        return card
    left_holder = tk.Frame(cards_frame, bg='#2a2a2a'); right_holder = tk.Frame(cards_frame, bg='#2a2a2a')
    left_holder.pack(side=tk.LEFT, padx=10); right_holder.pack(side=tk.LEFT, padx=10)
    def rotate_left():
        try:
            if not left_holder.winfo_exists():
                return
            for w in left_holder.winfo_children():
                try: w.destroy()
                except Exception: pass
            if featured:
                render_featured_card(left_holder, featured[app._featured_idx_left % len(featured)])
                app._featured_idx_left = (app._featured_idx_left + 1) % len(featured)
            delay = 5000 if getattr(app, '_left_first', True) else 10000
            app._left_first = False
            app.root.after(delay, rotate_left)
        except Exception:
            return
    def rotate_right():
        try:
            if not right_holder.winfo_exists():
                return
            for w in right_holder.winfo_children():
                try: w.destroy()
                except Exception: pass
            if featured:
                render_featured_card(right_holder, featured[app._featured_idx_right % len(featured)])
                app._featured_idx_right = (app._featured_idx_right + 1) % len(featured)
            app.root.after(10000, rotate_right)
        except Exception:
            return
    rotate_left(); app.root.after(10000, rotate_right)

    movies = db.execute_query("SELECT * FROM movies ORDER BY average_rating DESC", fetch_all=True)
    app.create_movie_grid(scrollable_frame, movies)

    testimonials_frame = tk.Frame(scrollable_frame, bg='#2a2a2a'); testimonials_frame.pack(fill=tk.X, padx=20, pady=20)
    tk.Label(testimonials_frame, text="What our users say", font=('Arial', 16, 'bold'), bg='#2a2a2a', fg='white').pack(pady=10)
    carousel = tk.Frame(testimonials_frame, bg='#2a2a2a'); carousel.pack(fill=tk.X)
    testimonials = [
        "Amazing experience! Smooth booking.",
        "Great selection of movies and shows!",
        "Seat selection UI is very intuitive.",
        "Wallet makes checkout fast.",
        "Love the watchlist feature!",
        "Customer service was helpful.",
        "Affordable pricing and clear sections.",
        "The UI looks clean and modern.",
        "Booking history is super handy.",
        "Highly recommend PQR Entertainment!",
    ]
    app._testi_idx = 0
    def render_testimonials():
        try:
            if not carousel.winfo_exists():
                return
            for w in carousel.winfo_children():
                try: w.destroy()
                except Exception: pass
            for i in range(3):
                idx = (app._testi_idx + i) % len(testimonials)
                card = tk.Frame(carousel, bg='#333', width=300, height=80); card.pack_propagate(False)
                card.pack(side=tk.LEFT, padx=10, pady=10)
                tk.Label(card, text='"' + testimonials[idx] + '"', wraplength=280, justify='left', bg='#333', fg='#ccc', font=('Arial', 10)).pack(padx=10, pady=10)
            app._testi_idx = (app._testi_idx + 3) % len(testimonials)
            app.root.after(10000, render_testimonials)
        except Exception:
            return
    render_testimonials()

    footer_frame = tk.Frame(scrollable_frame, bg='#2a2a2a'); footer_frame.pack(fill=tk.X, padx=20, pady=20)
    tk.Label(footer_frame, text="Contact Us: contact@pqrentertainment.com", font=('Arial', 10), bg='#2a2a2a', fg='#888').pack(pady=10)
    canvas.pack(side="left", fill="both", expand=True, padx=20); scrollbar.pack(side="right", fill="y")

def show_wallet(app):
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)
    user = db.execute_query("SELECT balance FROM users WHERE user_id = ?", (app.get_current_user()['user_id'],), fetch_one=True)
    app.get_current_user()['balance'] = user['balance']
    content_frame = tk.Frame(app.main_container, bg='#1a1a1a'); content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(content_frame, text="💰 My Wallet", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    balance_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2); balance_frame.pack(pady=20)
    tk.Label(balance_frame, text="Current Balance", font=('Arial', 14), bg='#2a2a2a', fg='#888').pack(pady=10, padx=50)
    tk.Label(balance_frame, text=f"₹{app.get_current_user()['balance']:.2f}", font=('Arial', 32, 'bold'), bg='#2a2a2a', fg='#4CAF50').pack(pady=10, padx=50)
    add_frame = tk.Frame(content_frame, bg='#1a1a1a'); add_frame.pack(pady=20)
    tk.Label(add_frame, text="Add Balance:", font=('Arial', 14), bg='#1a1a1a', fg='white').pack()
    quick_frame = tk.Frame(add_frame, bg='#1a1a1a'); quick_frame.pack(pady=10)
    for amount in [500,1000,2000,5000]:
        tk.Button(quick_frame, text=f"+ ₹{amount}", bg='#2196F3', fg='white', font=('Arial', 12), width=10, command=lambda a=amount: app.add_balance(a)).pack(side=tk.LEFT, padx=5)
    custom_frame = tk.Frame(add_frame, bg='#1a1a1a'); custom_frame.pack(pady=10)
    tk.Label(custom_frame, text="Custom Amount:", font=('Arial', 11), bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=5)
    amount_var = tk.StringVar(); tk.Entry(custom_frame, textvariable=amount_var, font=('Arial', 12), width=15).pack(side=tk.LEFT, padx=5)
    tk.Button(custom_frame, text="Add", bg='#4CAF50', fg='white', font=('Arial', 11), command=lambda: app.add_balance(float(amount_var.get() or 0))).pack(side=tk.LEFT, padx=5)

def show_watchlist(app):
    import json
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)
    content_frame = tk.Frame(app.main_container, bg='#1a1a1a'); content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(content_frame, text="⭐ My Watchlist", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    watchlist = db.execute_query(
        """SELECT w.*, m.title, m.average_rating, m.languages_json, m.genres_json
               FROM watchlist w JOIN movies m ON w.movie_id = m.movie_id
               WHERE w.user_id = ?""",
        (app.get_current_user()['user_id'],), fetch_all=True)
    if not watchlist:
        tk.Label(content_frame, text="Your watchlist is empty", font=('Arial', 14), bg='#1a1a1a', fg='#888').pack(pady=50)
        tk.Label(content_frame, text="Add movies from the homepage!", font=('Arial', 12), bg='#1a1a1a', fg='#888').pack()
        return

    canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    list_frame = tk.Frame(canvas, bg='#1a1a1a')
    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=list_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    for item in watchlist:
        item_frame = tk.Frame(list_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2); item_frame.pack(fill=tk.X, pady=10)
        info_frame = tk.Frame(item_frame, bg='#2a2a2a'); info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        tk.Label(info_frame, text=item['title'], font=('Arial', 14, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w')
        tk.Label(info_frame, text=f"⭐ {item['average_rating']}/5.0", font=('Arial', 11), bg='#2a2a2a', fg='#FFD700').pack(anchor='w')
        try:
            genres = json.loads(item.get('genres_json') or '[]')
            if genres:
                tk.Label(info_frame, text=', '.join(genres), font=('Arial', 10), bg='#2a2a2a', fg='#bbb').pack(anchor='w')
        except Exception:
            pass
        try:
            languages = json.loads(item['languages_json']); tk.Label(info_frame, text=', '.join(languages), font=('Arial', 10), bg='#2a2a2a', fg='#888').pack(anchor='w')
        except Exception:
            pass
        btn_frame = tk.Frame(item_frame, bg='#2a2a2a'); btn_frame.pack(side=tk.RIGHT, padx=20)
        movie = db.execute_query("SELECT * FROM movies WHERE movie_id = ?", (item['movie_id'],), fetch_one=True)
        tk.Button(btn_frame, text="Visit", bg='#4CAF50', fg='white', font=('Arial', 11), width=10, command=lambda m=movie: app.show_movie_detail(m)).pack(pady=5)
        tk.Button(btn_frame, text="Remove", bg='#f44336', fg='white', font=('Arial', 11), width=10, command=lambda mid=item['movie_id']: app.remove_from_watchlist_page(mid)).pack(pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def show_my_bookings(app):
    from datetime import datetime
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)
    content_frame = tk.Frame(app.main_container, bg='#1a1a1a'); content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(content_frame, text="🎫 My Bookings", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    bookings = db.execute_query(
        """SELECT b.*, m.title, ss.start_time, t.name as theatre_name, t.city, ss.screen_number
               FROM bookings b JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
               JOIN movies m ON ss.movie_id = m.movie_id JOIN theatres t ON ss.theatre_id = t.theatre_id
               WHERE b.user_id = ? AND DATE(ss.start_time) >= DATE('now') ORDER BY ss.start_time""",
        (app.get_current_user()['user_id'],), fetch_all=True)
    if not bookings:
        tk.Label(content_frame, text="No upcoming bookings", font=('Arial', 14), bg='#1a1a1a', fg='#888').pack(pady=50)
        return

    canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    list_frame = tk.Frame(canvas, bg='#1a1a1a')
    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=list_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    for booking in bookings:
        booking_frame = tk.Frame(list_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2); booking_frame.pack(fill=tk.X, pady=10)
        tk.Label(booking_frame, text=booking['title'], font=('Arial', 14, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=5)
        show_time = datetime.fromisoformat(booking['start_time']); time_str = show_time.strftime("%d %b %Y, %I:%M %p")
        tk.Label(booking_frame, text=f"📅 {time_str}", font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
        tk.Label(booking_frame, text=f"🏢 {booking['theatre_name']}, {booking['city']}", font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
        tk.Label(booking_frame, text=f"💺 Seat: {booking['seat']} | Screen: {booking['screen_number']}", font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
        tk.Label(booking_frame, text=f"💰 ₹{booking['amount']}", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='#4CAF50').pack(anchor='w', padx=20, pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def show_booking_history(app):
    from datetime import datetime
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)
    content_frame = tk.Frame(app.main_container, bg='#1a1a1a'); content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(content_frame, text="📜 Booking History", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    bookings = db.execute_query(
        """SELECT b.*, m.title, ss.start_time, t.name as theatre_name, t.city, ss.screen_number
               FROM bookings b JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
               JOIN movies m ON ss.movie_id = m.movie_id JOIN theatres t ON ss.theatre_id = t.theatre_id
               WHERE b.user_id = ? ORDER BY ss.start_time DESC""",
        (app.get_current_user()['user_id'],), fetch_all=True)
    if not bookings:
        tk.Label(content_frame, text="No bookings yet", font=('Arial', 14), bg='#1a1a1a', fg='#888').pack(pady=50)
        return
    canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0); scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='#1a1a1a'); scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
    for booking in bookings:
        show_time = datetime.fromisoformat(booking['start_time']); time_str = show_time.strftime("%d %b %Y, %I:%M %p")
        tk.Label(scrollable_frame, text=f"{booking['title']} | {time_str} | {booking['theatre_name']}, {booking['city']} | Seat: {booking['seat']} | ₹{booking['amount']}", font=('Arial', 10), bg='#1a1a1a', fg='#ccc', anchor='w').pack(fill=tk.X, padx=10, pady=5)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

def show_event_detail(app, event):
    app.current_event_id = event['event_id']
    popup = tk.Toplevel(app.root)
    popup.title(event['title'])
    popup.geometry("600x680")
    popup.configure(bg='#1a1a1a')
    canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
    detail_frame = tk.Frame(canvas, bg='#1a1a1a')
    detail_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=detail_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    tk.Label(detail_frame, text=event['title'], font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=(20,10))
    img_holder = tk.Frame(detail_frame, bg='#1a1a1a'); img_holder.pack()
    cover = event.get('cover_image_path') or f"assets/{event['title'].lower().replace(' ', '_').replace(':','')}.jpg"
    photo = app._load_asset_image(cover, (400, 250))
    if photo:
        tk.Label(img_holder, image=photo, bg='#1a1a1a').pack()
    tk.Label(detail_frame, text=f"⭐ {event.get('average_rating', 0)}/5.0", font=('Arial', 14), bg='#1a1a1a', fg='#FFD700').pack()
    if event.get('description'):
        desc = tk.Frame(detail_frame, bg='#2a2a2a'); desc.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(desc, text="About:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        tk.Label(desc, text=event['description'], font=('Arial', 11), bg='#2a2a2a', fg='#ccc', wraplength=500, justify='left').pack(anchor='w', padx=10, pady=5)
    try:
        performers = json.loads(event.get('performers_json') or '[]')
        if performers:
            pf = tk.Frame(detail_frame, bg='#2a2a2a'); pf.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(pf, text="Performers:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(pf, text=', '.join(performers), font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
    except Exception:
        pass
    try:
        genres = json.loads(event.get('genres_json') or '[]')
        if genres:
            gf = tk.Frame(detail_frame, bg='#2a2a2a'); gf.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(gf, text="Genres:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(gf, text=', '.join(genres), font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
    except Exception:
        pass
    wl = db.execute_query("SELECT * FROM watchlist WHERE user_id = ? AND event_id = ?", (app.get_current_user()['user_id'], event['event_id']), fetch_one=True)
    if wl:
        tk.Button(detail_frame, text="❤ Remove from Watchlist", bg='#f44336', fg='white', font=('Arial', 12), command=lambda: app.remove_from_watchlist_event(event['event_id'], popup)).pack(pady=10)
    else:
        tk.Button(detail_frame, text="❤ Add to Watchlist", bg='#FF9800', fg='white', font=('Arial', 12), command=lambda: app.add_to_watchlist_event(event['event_id'], popup)).pack(pady=10)
    tk.Button(detail_frame, text="🎫 Book Tickets", bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'), command=lambda: [popup.destroy(), app.show_city_selection_for_event()]).pack(pady=20)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

def show_movie_detail(app, movie):
    app.current_movie_id = movie['movie_id']
    popup = tk.Toplevel(app.root)
    popup.title(movie['title'])
    popup.geometry("600x700")
    popup.configure(bg='#1a1a1a')
    canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0)
    scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
    detail_frame = tk.Frame(canvas, bg='#1a1a1a')
    detail_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=detail_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    tk.Label(detail_frame, text=movie['title'], font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=(20,10))
    img_holder = tk.Frame(detail_frame, bg='#1a1a1a'); img_holder.pack()
    cover = movie.get('cover_image_path') or f"assets/{movie['title'].lower().replace(' ', '_').replace(':','')}.jpg"
    photo = app._load_asset_image(cover, (400, 250))
    if photo:
        tk.Label(img_holder, image=photo, bg='#1a1a1a').pack()
    tk.Label(detail_frame, text=f"⭐ {movie['average_rating']}/5.0", font=('Arial', 14), bg='#1a1a1a', fg='#FFD700').pack()
    if movie['description']:
        desc_frame = tk.Frame(detail_frame, bg='#2a2a2a'); desc_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        tk.Label(desc_frame, text=movie['description'], font=('Arial', 11), bg='#2a2a2a', fg='#ccc', wraplength=500, justify='left').pack(anchor='w', padx=10, pady=5)
    try:
        actors = json.loads(movie['actors_json'])
        actors_frame = tk.Frame(detail_frame, bg='#2a2a2a'); actors_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(actors_frame, text="Cast:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        tk.Label(actors_frame, text=', '.join(actors), font=('Arial', 11), bg='#2a2a2a', fg='#ccc', wraplength=500).pack(anchor='w', padx=10, pady=5)
    except Exception:
        pass
    try:
        languages = json.loads(movie['languages_json'])
        lang_frame = tk.Frame(detail_frame, bg='#2a2a2a'); lang_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(lang_frame, text="Languages:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        tk.Label(lang_frame, text=', '.join(languages), font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
    except Exception:
        pass
    try:
        genres = json.loads(movie['genres_json'])
        genre_frame = tk.Frame(detail_frame, bg='#2a2a2a'); genre_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(genre_frame, text="Genres:", font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        tk.Label(genre_frame, text=', '.join(genres), font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
    except Exception:
        pass
    duration_mins = movie['duration_seconds'] // 60
    hours = duration_mins // 60; mins = duration_mins % 60
    duration_frame = tk.Frame(detail_frame, bg='#2a2a2a'); duration_frame.pack(fill=tk.X, padx=20, pady=10)
    tk.Label(duration_frame, text=f"Duration: {hours}h {mins}m", font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
    watchlist_check = db.execute_query("SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?", (app.get_current_user()['user_id'], movie['movie_id']), fetch_one=True)
    if watchlist_check:
        tk.Button(detail_frame, text="❤ Remove from Watchlist", bg='#f44336', fg='white', font=('Arial', 12), command=lambda: app.remove_from_watchlist(movie['movie_id'], popup)).pack(pady=10)
    else:
        tk.Button(detail_frame, text="❤ Add to Watchlist", bg='#FF9800', fg='white', font=('Arial', 12), command=lambda: app.add_to_watchlist(movie['movie_id'], popup)).pack(pady=10)
    tk.Button(detail_frame, text="🎫 Book Tickets", bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'), command=lambda: [popup.destroy(), app.show_city_selection()]).pack(pady=20)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

def show_city_selection_for_event(app):
    popup = tk.Toplevel(app.root); popup.title("Select City"); popup.geometry("400x300"); popup.configure(bg='#1a1a1a')
    tk.Label(popup, text="Select City", font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    for city in ['Mumbai','Pune','Nashik','Bangalore']:
        tk.Button(popup, text=city, font=('Arial', 14), bg='#2196F3', fg='white', width=20, command=lambda c=city: [popup.destroy(), app.show_theatre_listing_for_event(c)]).pack(pady=10)

def show_theatre_listing_for_event(app, city):
    query = (
        """
        SELECT ss.*, t.name as theatre_name, t.seating_schema_json, t.hall_type as hall_type, e.title as event_title
        FROM scheduled_screens ss
        JOIN theatres t ON ss.theatre_id = t.theatre_id
        JOIN events e ON ss.event_id = e.event_id
        WHERE t.city = ? AND ss.event_id = ?
        AND DATE(ss.start_time) >= DATE('now')
        AND DATE(ss.start_time) <= DATE('now', '+3 days')
        ORDER BY ss.start_time
        """
    )
    screens = db.execute_query(query, (city, app.current_event_id), fetch_all=True)
    if not screens:
        from tkinter import messagebox
        messagebox.showinfo("No Shows", f"No shows available in {city} for this event.")
        return
    popup = tk.Toplevel(app.root); popup.title(f"Venues in {city}"); popup.geometry("700x600"); popup.configure(bg='#1a1a1a')
    tk.Label(popup, text=f"Venues in {city}", font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(pady=10)
    tk.Label(popup, text=screens[0]['event_title'], font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0); scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
    theatre_frame = tk.Frame(canvas, bg='#1a1a1a'); theatre_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=theatre_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
    theatres = {}
    for screen in screens:
        theatres.setdefault(screen['theatre_name'], []).append(screen)
    for theatre_name, shows in theatres.items():
        theatre_card = tk.Frame(theatre_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2); theatre_card.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(theatre_card, text=theatre_name, font=('Arial', 14, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        for show in shows:
            show_time = datetime.fromisoformat(show['start_time']); time_str = show_time.strftime("%d %b, %I:%M %p")
            try:
                seat_map = json.loads(show['seat_map_json']); booked = sum(row.count(1) for row in seat_map); available = 100 - booked
            except Exception:
                available = 100
            show_frame = tk.Frame(theatre_card, bg='#333'); show_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(show_frame, text=f"{time_str} | Screen {show['screen_number']}", font=('Arial', 11), bg='#333', fg='white').pack(side=tk.LEFT, padx=10)
            tk.Label(show_frame, text=f"{available} seats", font=('Arial', 10), bg='#333', fg='#4CAF50').pack(side=tk.LEFT, padx=10)
            tk.Button(show_frame, text="Select", bg='#4CAF50', fg='white', command=lambda s=show: [popup.destroy(), app.show_seat_selection(s)]).pack(side=tk.RIGHT, padx=10)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

def show_city_selection(app):
    popup = tk.Toplevel(app.root); popup.title("Select City"); popup.geometry("400x300"); popup.configure(bg='#1a1a1a')
    tk.Label(popup, text="Select City", font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(pady=20)
    for city in ['Mumbai','Pune','Nashik','Bangalore']:
        tk.Button(popup, text=city, font=('Arial', 14), bg='#2196F3', fg='white', width=20, command=lambda c=city: [popup.destroy(), app.show_theatre_listing(c)]).pack(pady=10)

def show_theatre_listing(app, city):
    query = (
        """
        SELECT ss.*, t.name as theatre_name, t.seating_schema_json, t.hall_type as hall_type, m.title as movie_title
        FROM scheduled_screens ss
        JOIN theatres t ON ss.theatre_id = t.theatre_id
        JOIN movies m ON ss.movie_id = m.movie_id
        WHERE t.city = ? AND ss.movie_id = ?
        AND DATE(ss.start_time) >= DATE('now')
        AND DATE(ss.start_time) <= DATE('now', '+3 days')
        ORDER BY ss.start_time
        """
    )
    screens = db.execute_query(query, (city, app.current_movie_id), fetch_all=True)
    if not screens:
        from tkinter import messagebox
        messagebox.showinfo("No Shows", f"No shows available in {city} for this movie.")
        return
    popup = tk.Toplevel(app.root); popup.title(f"Theatres in {city}"); popup.geometry("700x600"); popup.configure(bg='#1a1a1a')
    tk.Label(popup, text=f"Theatres in {city}", font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(pady=10)
    tk.Label(popup, text=screens[0]['movie_title'], font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0); scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
    theatre_frame = tk.Frame(canvas, bg='#1a1a1a'); theatre_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=theatre_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
    theatres = {}
    for screen in screens:
        theatres.setdefault(screen['theatre_name'], []).append(screen)
    for theatre_name, shows in theatres.items():
        theatre_card = tk.Frame(theatre_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2); theatre_card.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(theatre_card, text=theatre_name, font=('Arial', 14, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
        for show in shows:
            show_time = datetime.fromisoformat(show['start_time']); time_str = show_time.strftime("%d %b, %I:%M %p")
            try:
                seat_map = json.loads(show['seat_map_json']); booked = sum(row.count(1) for row in seat_map); available = 100 - booked
            except Exception:
                available = 100
            show_frame = tk.Frame(theatre_card, bg='#333'); show_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(show_frame, text=f"{time_str} | Screen {show['screen_number']}", font=('Arial', 11), bg='#333', fg='white').pack(side=tk.LEFT, padx=10)
            tk.Label(show_frame, text=f"{available} seats", font=('Arial', 10), bg='#333', fg='#4CAF50').pack(side=tk.LEFT, padx=10)
            tk.Button(show_frame, text="Select", bg='#4CAF50', fg='white', command=lambda s=show: [popup.destroy(), app.show_seat_selection(s)]).pack(side=tk.RIGHT, padx=10)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

def show_seat_selection(app, screen_data):
    app.current_screen_id = screen_data['screen_id']
    app.selected_seats = []
    popup = tk.Toplevel(app.root); popup.title("Select Seats"); popup.geometry("900x700"); popup.configure(bg='#1a1a1a')
    header_frame = tk.Frame(popup, bg='#2a2a2a'); header_frame.pack(fill=tk.X)
    tk.Label(header_frame, text="Select Your Seats", font=('Arial', 18, 'bold'), bg='#2a2a2a', fg='white').pack(pady=10)
    show_time = datetime.fromisoformat(screen_data['start_time']); time_str = show_time.strftime("%d %b %Y, %I:%M %p")
    tk.Label(header_frame, text=f"{screen_data['theatre_name']} - Screen {screen_data['screen_number']}", font=('Arial', 12), bg='#2a2a2a', fg='#888').pack()
    tk.Label(header_frame, text=time_str, font=('Arial', 11), bg='#2a2a2a', fg='#888').pack(pady=5)
    screen_label_frame = tk.Frame(popup, bg='#1a1a1a'); screen_label_frame.pack(pady=20)
    tk.Label(screen_label_frame, text="═══════════ SCREEN ═══════════", font=('Arial', 14, 'bold'), bg='#1a1a1a', fg='white').pack()
    seat_frame = tk.Frame(popup, bg='#1a1a1a'); seat_frame.pack(pady=20)
    try:
        seat_map = json.loads(screen_data['seat_map_json'])
    except Exception:
        seat_map = [[0 for _ in range(10)] for _ in range(10)]
    price_economy = screen_data['price_economy']; price_central = screen_data['price_central']; price_premium = screen_data['price_premium']
    hall_type = (screen_data.get('hall_type') or 'cinema').lower()
    rows = ['J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
    for row_idx, row_label in enumerate(rows):
        tk.Label(seat_frame, text=row_label, font=('Arial', 12, 'bold'), bg='#1a1a1a', fg='white').grid(row=row_idx, column=0, padx=5)
        for col in range(10):
            seat_num = f"{row_label}{col+1}"; is_booked = seat_map[row_idx][col] == 1
            if hall_type == 'stage':
                if row_idx < 3: price = price_economy
                elif row_idx < 7: price = price_central
                else: price = price_premium
            else:
                if row_idx < 3: price = price_premium
                elif row_idx < 7: price = price_central
                else: price = price_economy
            btn = tk.Button(seat_frame, text=seat_num, width=6, height=2, bg='#666' if is_booked else '#fff', fg='white' if is_booked else 'black', state=tk.DISABLED if is_booked else tk.NORMAL)
            btn.grid(row=row_idx, column=col+1, padx=2, pady=2)
            if not is_booked:
                btn.config(command=lambda b=btn, s=seat_num, p=price: app.toggle_seat(b, s, p))
    legend_frame = tk.Frame(popup, bg='#1a1a1a'); legend_frame.pack(pady=10)
    tk.Label(legend_frame, text="■ Available", bg='#1a1a1a', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
    tk.Label(legend_frame, text="■ Selected", bg='#4CAF50', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
    tk.Label(legend_frame, text="■ Booked", bg='#666', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
    price_frame = tk.Frame(popup, bg='#2a2a2a'); price_frame.pack(fill=tk.X, pady=10)
    tk.Label(price_frame, text=f"Economy (A-C): ₹{price_economy}  |  Central (D-G): ₹{price_central}  |  Recliner (H-J): ₹{price_premium}", font=('Arial', 11), bg='#2a2a2a', fg='white').pack(pady=5)
    bottom_frame = tk.Frame(popup, bg='#1a1a1a'); bottom_frame.pack(fill=tk.X, pady=20)
    app.total_label = tk.Label(bottom_frame, text="Total: ₹0", font=('Arial', 16, 'bold'), bg='#1a1a1a', fg='white'); app.total_label.pack(side=tk.LEFT, padx=20)
    tk.Button(bottom_frame, text="Proceed to Payment", bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'), command=lambda: [popup.destroy(), app.process_payment(screen_data)]).pack(side=tk.RIGHT, padx=20)
