"""
Theatre Booking Management System - Complete Application
PQR Entertainment PaaS Desktop Application

Entry point: main.py
Packaging: pyinstaller --onefile --noconsole main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dbwrap import db
from datetime import datetime
import json
import os
import math
import threading
import re
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except Exception:
    FigureCanvasTkAgg = None
    plt = None
try:
    from backend import scheduling as sched
except Exception:
    sched = None
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None
try:
    from frontend import assets as ui_assets
except Exception:
    ui_assets = None
try:
    from frontend import pages_admin
except Exception:
    pages_admin = None

# Global state
current_user = None
current_role = None
admin_stack = []
producer_stack = []
user_stack = []
admin_forward_stack = []
producer_forward_stack = []
user_forward_stack = []
menu_visible = False


class theatre_booking_app:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PQR Entertainment - Theatre Booking System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Main container
        self.main_container = tk.Frame(root, bg='#1a1a1a')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Menu overlay (initially hidden)
        self.menu_overlay = None
        
        # Current movie for booking
        self.current_movie_id = None
        self.current_screen_id = None
        self.selected_seats = []
        self.current_event_id = None
        self.image_cache = []  # keep references to PhotoImage
        
        # Ensure default admin user exists (auto seeding/sync disabled)
        try:
            self._ensure_default_admin()
        except Exception:
            pass
        
        # Start with login page
        self.show_login_page()
    
    def clear_container(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
        global menu_visible
        menu_visible = False

    def show_toast(self, message, duration_ms=2000, bg="#323232", fg="white"):
        """Show a transient toast message overlay (delegates to frontend.assets)"""
        if ui_assets:
            try:
                ui_assets.show_toast(self.root, message, duration_ms, bg, fg)
                return
            except Exception:
                pass

    def _ensure_default_admin(self):
        """Create a default admin if not present (snaksartrate/password)"""
        existing = db.execute_query(
            "SELECT user_id FROM users WHERE username = ?",
            ("snaksartrate",), fetch_one=True
        )
        if not existing:
            db.execute_query(
                "INSERT INTO users (username, password, role, name, email, balance) VALUES (?, ?, 'admin', ?, ?, 0)",
                ("snaksartrate", "password", "Administrator", "admin@example.com")
            )

    def _seed_producers_and_reassign(self):
        """Ensure producer2/3/4 exist and assign ownership per rules:
        - All movies -> producer2 initially
        - All events -> producer3
        - Half of movies -> producer4 (override some of producer2)
        """
        # Helper to ensure producer user+profile
        def ensure_producer(username, display_name):
            user = db.execute_query("SELECT * FROM users WHERE username=?", (username,), fetch_one=True)
            if not user:
                uid = db.execute_query(
                    "INSERT INTO users (username, password, role, name, email, balance) VALUES (?, 'password', 'producer', ?, ?, 0)",
                    (username, display_name, f"{username}@example.com")
                )
                user = db.execute_query("SELECT * FROM users WHERE user_id=?", (uid,), fetch_one=True)
            # producer profile
            prof = db.execute_query("SELECT * FROM producers WHERE user_id=?", (user['user_id'],), fetch_one=True)
            if not prof:
                pid = db.execute_query("INSERT INTO producers (user_id, name, details) VALUES (?, ?, ?)", (user['user_id'], display_name, ""))
                prof = db.execute_query("SELECT * FROM producers WHERE producer_id=?", (pid,), fetch_one=True)
            return prof['producer_id']

        p2_id = ensure_producer('producer2', 'Producer 2')
        p3_id = ensure_producer('producer3', 'Producer 3')
        p4_id = ensure_producer('producer4', 'Producer 4')

        # Assign all movies to producer2
        db.execute_query("UPDATE movies SET producer_id=?", (p2_id,))
        # Assign all events to producer3 (events use host_id)
        try:
            db.execute_query("UPDATE events SET host_id=?", (p3_id,))
        except Exception:
            pass
        # Assign half of movies to producer4
        movies = db.execute_query("SELECT movie_id FROM movies ORDER BY movie_id", fetch_all=True)
        if movies:
            half = movies[::2]  # every second movie
            for row in half:
                db.execute_query("UPDATE movies SET producer_id=? WHERE movie_id=?", (p4_id, row['movie_id']))

    def export_credentials_to_file(self):
        """Export all usernames/passwords/roles to tbms2/demo_credentials.txt"""
        users = db.execute_query("SELECT username, password, role FROM users ORDER BY role, username", fetch_all=True)
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            out_path = os.path.join(base_dir, 'demo_credentials.txt')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write('Demo credentials (exported)\n\n')
                roles = {'admin': [], 'producer': [], 'user': []}
                for u in users or []:
                    roles.setdefault(u['role'], []).append((u['username'], u['password']))
                if roles.get('user'):
                    f.write('[Users]\n')
                    for uname, pwd in roles['user']:
                        f.write(f'- {uname} / {pwd}\n')
                    f.write('\n')
                if roles.get('producer'):
                    f.write('[Producer]\n')
                    for uname, pwd in roles['producer']:
                        f.write(f'- {uname} / {pwd}\n')
                    f.write('\n')
                if roles.get('admin'):
                    f.write('[Admin]\n')
                    for uname, pwd in roles['admin']:
                        f.write(f'- {uname} / {pwd}\n')
                    f.write('\n')
        except Exception:
            pass

    def _normalize_username(self, uname):
        """Lowercase and validate username against rules: a-z, 0-9, ., _, 3-20 chars."""
        if not isinstance(uname, str):
            return None
        uname = uname.strip().lower()
        if re.fullmatch(r"[a-z0-9._]{3,20}", uname):
            return uname
        return None

    def _parse_demo_credentials(self):
        """Parse demo_credentials.txt into role->set(usernames). Ignores invalid lines."""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            in_path = os.path.join(base_dir, 'demo_credentials.txt')
            if not os.path.exists(in_path):
                return {'admin': set(), 'producer': set(), 'user': set()}
            section = None
            roles = {'admin': set(), 'producer': set(), 'user': set()}
            with open(in_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        tag = line[1:-1].strip().lower()
                        if tag == 'users':
                            section = 'user'
                        elif tag == 'producer':
                            section = 'producer'
                        elif tag == 'admin':
                            section = 'admin'
                        else:
                            section = None
                        continue
                    if line.startswith('-') and section:
                        try:
                            part = line[1:].strip()
                            if ' / ' in part:
                                uname = part.split(' / ')[0].strip()
                            else:
                                uname = part
                            norm = self._normalize_username(uname)
                            if norm:
                                roles[section].add(norm)
                        except Exception:
                            continue
            return roles
        except Exception:
            return {'admin': set(), 'producer': set(), 'user': set()}

    def _ensure_producer_profile(self, user_id, display_name=None):
        """Ensure producers row exists for given user; return producer_id."""
        prof = db.execute_query("SELECT * FROM producers WHERE user_id=?", (user_id,), fetch_one=True)
        if prof:
            return prof['producer_id']
        if not display_name:
            # derive a basic name from the username
            user = db.execute_query("SELECT * FROM users WHERE user_id=?", (user_id,), fetch_one=True)
            uname = user['username'] if user else 'producer'
            display_name = uname.replace('.', ' ').replace('_', ' ').title()
        pid = db.execute_query("INSERT INTO producers (user_id, name, details) VALUES (?, ?, ?)", (user_id, display_name, ""))
        return pid

    def _create_user(self, username, role, password='pass123', name=None, email=None):
        if not name:
            name = username.replace('.', ' ').replace('_', ' ').title()
        if not email:
            email = f"{username}@example.com"
        uid = db.execute_query(
            "INSERT INTO users (username, password, role, name, email, balance) VALUES (?, ?, ?, ?, ?, 0)",
            (username, password, role, name, email)
        )
        return uid

    def _ensure_owner_user_for_producer_name(self, producer_name):
        """Given a producer/display name, ensure a user+producer exist and return producer_id."""
        uname = re.sub(r"[^a-z0-9._]", '_', producer_name.strip().lower().replace(' ', '_'))
        uname = re.sub(r"_+", '_', uname)
        uname = uname.strip('_')
        if not self._normalize_username(uname):
            # fallback with prefix
            base = re.sub(r"[^a-z0-9._]", '', producer_name.strip().lower()) or 'producer'
            uname = (base[:12] + '_prod')[:20]
        user = db.execute_query("SELECT * FROM users WHERE username=?", (uname,), fetch_one=True)
        if not user:
            uid = self._create_user(uname, 'producer', 'pass123')
        else:
            uid = user['user_id']
            # ensure role and password
            db.execute_query("UPDATE users SET role='producer', password='pass123' WHERE user_id=?", (uid,))
        pid = self._ensure_producer_profile(uid, producer_name)
        return pid

    def sync_from_demo_credentials(self):
        """Synchronize DB to demo_credentials.txt and fix orphaned content owners.
        - Delete users not in the file
        - Set all listed users passwords to pass123 and correct role
        - Ensure producers/hosts exist and link to movies/events
        - Update demo_credentials.txt afterwards
        """
        roles = self._parse_demo_credentials()
        allowed = roles['admin'] | roles['producer'] | roles['user']
        # 1) Delete users not listed
        all_users = db.execute_query("SELECT * FROM users", fetch_all=True) or []
        for u in all_users:
            uname = u['username']
            if uname not in allowed:
                # clean dependents
                try:
                    db.execute_query("DELETE FROM bookings WHERE user_id=?", (u['user_id'],))
                    db.execute_query("DELETE FROM feedbacks WHERE user_id=?", (u['user_id'],))
                    db.execute_query("DELETE FROM watchlist WHERE user_id=?", (u['user_id'],))
                    db.execute_query("DELETE FROM producers WHERE user_id=?", (u['user_id'],))
                except Exception:
                    pass
                db.execute_query("DELETE FROM users WHERE user_id=?", (u['user_id'],))

        # 2) Ensure listed users exist with correct role and password
        for uname in roles['admin']:
            existing = db.execute_query("SELECT * FROM users WHERE username=?", (uname,), fetch_one=True)
            if not existing:
                self._create_user(uname, 'admin', 'pass123')
            else:
                db.execute_query("UPDATE users SET role='admin', password='pass123' WHERE user_id=?", (existing['user_id'],))
        for uname in roles['producer']:
            existing = db.execute_query("SELECT * FROM users WHERE username=?", (uname,), fetch_one=True)
            if not existing:
                uid = self._create_user(uname, 'producer', 'pass123')
            else:
                uid = existing['user_id']
                db.execute_query("UPDATE users SET role='producer', password='pass123' WHERE user_id=?", (uid,))
            self._ensure_producer_profile(uid)
        for uname in roles['user']:
            existing = db.execute_query("SELECT * FROM users WHERE username=?", (uname,), fetch_one=True)
            if not existing:
                self._create_user(uname, 'user', 'pass123')
            else:
                db.execute_query("UPDATE users SET role='user', password='pass123' WHERE user_id=?", (existing['user_id'],))

        # 3) Fix movies: ensure producer exists
        movies = db.execute_query("SELECT movie_id, producer_id FROM movies", fetch_all=True) or []
        for m in movies:
            prod = None
            if m['producer_id']:
                prod = db.execute_query("SELECT * FROM producers WHERE producer_id=?", (m['producer_id'],), fetch_one=True)
            if not prod:
                # Create a new producer owner specific to this movie
                pname = f"Producer Movie {m['movie_id']}"
                new_pid = self._ensure_owner_user_for_producer_name(pname)
                db.execute_query("UPDATE movies SET producer_id=? WHERE movie_id=?", (new_pid, m['movie_id']))
            else:
                # ensure producer has a backing user
                u = db.execute_query("SELECT * FROM users WHERE user_id=?", (prod['user_id'],), fetch_one=True)
                if not u:
                    pname = prod.get('name') or f"Producer Movie {m['movie_id']}"
                    new_pid = self._ensure_owner_user_for_producer_name(pname)
                    db.execute_query("UPDATE movies SET producer_id=? WHERE movie_id=?", (new_pid, m['movie_id']))

        # 4) Fix events: ensure host exists (producers table is reused as hosts)
        try:
            events = db.execute_query("SELECT event_id, host_id FROM events", fetch_all=True) or []
            for e in events:
                host = None
                if e['host_id']:
                    host = db.execute_query("SELECT * FROM producers WHERE producer_id=?", (e['host_id'],), fetch_one=True)
                if not host:
                    hname = f"Host Event {e['event_id']}"
                    new_pid = self._ensure_owner_user_for_producer_name(hname)
                    db.execute_query("UPDATE events SET host_id=? WHERE event_id=?", (new_pid, e['event_id']))
                else:
                    u = db.execute_query("SELECT * FROM users WHERE user_id=?", (host['user_id'],), fetch_one=True)
                    if not u:
                        hname = host.get('name') or f"Host Event {e['event_id']}"
                        new_pid = self._ensure_owner_user_for_producer_name(hname)
                        db.execute_query("UPDATE events SET host_id=? WHERE event_id=?", (new_pid, e['event_id']))
        except Exception:
            pass

        # 5) Update credentials file to reflect current users
        try:
            self.export_credentials_to_file()
        except Exception:
            pass
    
    def show_login_page(self):
        """Simple login screen; routes to role home on success"""
        self.clear_container()
        center = tk.Frame(self.main_container, bg='#1a1a1a')
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        tk.Label(center, text="Login", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=10)
        form = tk.Frame(center, bg='#2a2a2a', padx=30, pady=30)
        form.pack(pady=10)
        tk.Label(form, text="Username", bg='#2a2a2a', fg='white', font=('Arial', 11)).grid(row=0, column=0, sticky='w')
        username_var = tk.StringVar()
        tk.Entry(form, textvariable=username_var, font=('Arial', 11), width=28).grid(row=0, column=1, padx=10, pady=5)
        tk.Label(form, text="Password", bg='#2a2a2a', fg='white', font=('Arial', 11)).grid(row=1, column=0, sticky='w')
        password_var = tk.StringVar()
        tk.Entry(form, textvariable=password_var, font=('Arial', 11), width=28, show='*').grid(row=1, column=1, padx=10, pady=5)

        def do_login():
            uname = username_var.get().strip()
            pwd = password_var.get().strip()
            if not uname or not pwd:
                messagebox.showerror("Error", "Enter username and password")
                return
            # Basic username/password validation
            import re
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", uname):
                messagebox.showerror("Error", "Username must be 3-20 chars (letters, numbers, underscore)")
                return
            if len(pwd) < 6 or not re.search(r"[A-Za-z]", pwd) or not re.search(r"\d", pwd):
                messagebox.showerror("Error", "Password must be at least 6 chars with letters and numbers")
                return
            user = db.execute_query(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (uname, pwd), fetch_one=True
            )
            if not user:
                messagebox.showerror("Error", "Invalid credentials")
                return
            global current_user, current_role, admin_stack, producer_stack, user_stack
            current_user = dict(user)
            current_role = user['role']
            # reset stacks and navigate
            admin_stack = []; producer_stack = []; user_stack = []
            if current_role == 'admin':
                self.add_navigation_bar(); self.add_header(show_menu=True, show_username=True)
                self.navigate_to('screen_manager')
            elif current_role == 'producer':
                self.add_navigation_bar(); self.add_header(show_menu=True, show_username=True)
                self.navigate_to('producer_dashboard')
            else:
                self.add_navigation_bar(); self.add_header(show_menu=True, show_username=True)
                self.navigate_to('user_home')

        tk.Button(center, text="Login", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=do_login).pack(pady=10)
        btns = tk.Frame(center, bg='#1a1a1a'); btns.pack()
        tk.Button(btns, text="Register as User", bg='#555', fg='white', command=lambda: self.show_register_page('user')).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Register as Producer", bg='#555', fg='white', command=lambda: self.show_register_page('producer')).pack(side=tk.LEFT, padx=5)

    def logout(self):
        """Logout and return to login screen"""
        global current_user, current_role, admin_stack, producer_stack, user_stack, admin_forward_stack, producer_forward_stack, user_forward_stack
        current_user = None
        current_role = None
        admin_stack = []; producer_stack = []; user_stack = []
        admin_forward_stack = []; producer_forward_stack = []; user_forward_stack = []
        self.show_login_page()

    def add_navigation_bar(self):
        """Add navigation bar with forward/backward/refresh buttons"""
        nav_frame = tk.Frame(self.main_container, bg='#2a2a2a', height=40)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        
        btn_style = {'bg': '#444', 'fg': 'white', 'font': ('Arial', 10), 
                     'borderwidth': 0, 'padx': 10, 'pady': 5}
        
        tk.Button(nav_frame, text="← Back", command=self.go_back, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="→ Forward", command=self.go_forward, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="↻ Refresh", command=self.refresh_page, **btn_style).pack(side=tk.LEFT, padx=5)
    
    def add_header(self, show_menu=True, show_search=False, show_username=True):
        """Add header with hamburger menu, search, and username"""
        header_frame = tk.Frame(self.main_container, bg='#2a2a2a', height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        if show_menu:
            menu_btn = tk.Button(header_frame, text="☰", font=('Arial', 20), 
                                bg='#2a2a2a', fg='white', borderwidth=0,
                                command=self.toggle_menu)
            menu_btn.pack(side=tk.LEFT, padx=20)
        
        title_label = tk.Label(header_frame, text="PQR Entertainment", 
                              font=('Arial', 16, 'bold'), bg='#2a2a2a', fg='white')
        title_label.pack(side=tk.LEFT, padx=20)
        
        if show_search:
            search_frame = tk.Frame(header_frame, bg='#2a2a2a')
            search_frame.pack(side=tk.LEFT, padx=20, expand=True)
            
            self.search_var = tk.StringVar()
            search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                   font=('Arial', 12), width=30)
            search_entry.pack(side=tk.LEFT, padx=5)
            
            # Genre filter dropdown
            genres = self.get_all_genres()
            self.genre_var = tk.StringVar(value='All')
            ttk.Combobox(search_frame, textvariable=self.genre_var, values=['All'] + genres, width=18, state='readonly').pack(side=tk.LEFT, padx=10)
            
            tk.Button(search_frame, text="Search", bg='#4CAF50', fg='white',
                     font=('Arial', 10), command=self.perform_search).pack(side=tk.LEFT)
        
        if show_username and current_user:
            user_label = tk.Label(header_frame, text=f"Welcome, {current_user['name']}", 
                                 font=('Arial', 12), bg='#2a2a2a', fg='white')
            user_label.pack(side=tk.RIGHT, padx=20)
            
            logout_btn = tk.Button(header_frame, text="Logout", bg='#d32f2f', fg='white',
                                  font=('Arial', 10), command=self.logout)
            logout_btn.pack(side=tk.RIGHT, padx=10)
    
    def toggle_menu(self):
        """Toggle hamburger menu overlay"""
        global menu_visible
        
        if menu_visible:
            if self.menu_overlay:
                self.menu_overlay.destroy()
                self.menu_overlay = None
            menu_visible = False
        else:
            self.show_menu_overlay()
            menu_visible = True
    
    def show_menu_overlay(self):
        """Show menu overlay based on role"""
        self.menu_overlay = tk.Frame(self.root, bg='#2a2a2a', width=300)
        self.menu_overlay.place(x=0, y=0, relheight=1)
        
        # Close button
        close_btn = tk.Button(self.menu_overlay, text="✕", font=('Arial', 16),
                             bg='#2a2a2a', fg='white', borderwidth=0,
                             command=self.toggle_menu)
        close_btn.pack(anchor=tk.NE, padx=10, pady=10)
        
        menu_style = {'bg': '#2a2a2a', 'fg': 'white', 'font': ('Arial', 12),
                     'borderwidth': 0, 'pady': 10, 'anchor': 'w', 'padx': 20}
        
        if current_role == 'user':
            tk.Button(self.menu_overlay, text="🏠 Home", 
                     command=lambda: self.navigate_to('user_home'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="👤 Profile", 
                     command=lambda: self.navigate_to('user_profile'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎫 My Bookings", 
                     command=lambda: self.navigate_to('my_bookings'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📜 Booking History", 
                     command=lambda: self.navigate_to('booking_history'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="⭐ Watchlist", 
                     command=lambda: self.navigate_to('watchlist'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎭 Events", 
                     command=lambda: self.navigate_to('events'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="💰 Wallet", 
                     command=lambda: self.navigate_to('wallet'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📝 Feedback", 
                     command=lambda: self.navigate_to('feedback'), **menu_style).pack(fill=tk.X)
            
            # Customer service info
            tk.Label(self.menu_overlay, text="Customer Service:", 
                    bg='#2a2a2a', fg='#888', font=('Arial', 9)).pack(pady=(20, 5))
            tk.Label(self.menu_overlay, text="customerservice@pqrentertainment.com", 
                    bg='#2a2a2a', fg='#4CAF50', font=('Arial', 8)).pack()
            
        elif current_role == 'producer':
            tk.Button(self.menu_overlay, text="🏠 Dashboard", 
                     command=lambda: self.navigate_to('producer_dashboard'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="➕ Add Movie/Event", 
                     command=lambda: self.navigate_to('add_content'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📊 Analytics", 
                     command=lambda: self.navigate_to('producer_analytics'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="👤 Profile", 
                     command=lambda: self.navigate_to('producer_profile'), **menu_style).pack(fill=tk.X)
            
        elif current_role == 'admin':
            tk.Button(self.menu_overlay, text="👤 Profile", 
                     command=lambda: self.navigate_to('admin_profile'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎬 Cinema Halls", 
                     command=lambda: self.navigate_to('cinema_halls'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="👥 Employees", 
                     command=lambda: self.navigate_to('employees'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📺 Screen Manager", 
                     command=lambda: self.navigate_to('screen_manager'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎬 Manage Movies", 
                     command=lambda: self.navigate_to('manage_movies'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="💬 Feedback", 
                     command=lambda: self.navigate_to('admin_feedback'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📊 Analytics", 
                     command=lambda: self.navigate_to('admin_analytics'), **menu_style).pack(fill=tk.X)
        
        tk.Button(self.menu_overlay, text="🚪 Logout", 
                 command=self.logout, bg='#d32f2f', fg='white', 
                 font=('Arial', 12), pady=10).pack(side=tk.BOTTOM, fill=tk.X)
    
    def navigate_to(self, page_name):
        """Navigate to a specific page"""
        if self.menu_overlay:
            self.toggle_menu()
        
        # Add to navigation stack
        global current_role, admin_stack, producer_stack, user_stack, admin_forward_stack, producer_forward_stack, user_forward_stack
        if current_role == 'admin':
            admin_stack.append(page_name)
            admin_forward_stack.clear()
        elif current_role == 'producer':
            producer_stack.append(page_name)
            producer_forward_stack.clear()
        elif current_role == 'user':
            user_stack.append(page_name)
            user_forward_stack.clear()
        
        # Route to appropriate page
        self.route_to(page_name)

    def route_to(self, page_name):
        """Route to page without altering history stacks"""
        routes = {
            'user_home': self.show_user_home,
            'user_profile': self.show_user_profile,
            'my_bookings': self.show_my_bookings,
            'booking_history': self.show_booking_history,
            'watchlist': self.show_watchlist,
            'wallet': self.show_wallet,
            'feedback': self.show_feedback_form,
            'events': self.show_events_page,
            'producer_dashboard': self.show_producer_dashboard,
            'add_content': self.show_add_content,
            'producer_analytics': self.show_producer_analytics,
            'admin_profile': self.show_admin_profile,
            'cinema_halls': self.show_cinema_halls,
            'employees': self.show_employees,
            'screen_manager': self.show_screen_manager,
            'admin_feedback': self.show_admin_feedback,
            'admin_analytics': self.show_admin_analytics,
            'manage_movies': self.show_manage_movies,
        }
        if page_name in routes:
            routes[page_name]()
    
    def get_stacks(self):
        """Return (history_stack, forward_stack) based on current role"""
        global current_role, admin_stack, producer_stack, user_stack, admin_forward_stack, producer_forward_stack, user_forward_stack
        if current_role == 'admin':
            return admin_stack, admin_forward_stack
        elif current_role == 'producer':
            return producer_stack, producer_forward_stack
        else:
            return user_stack, user_forward_stack

    def go_back(self):
        """Navigate backward"""
        stack, fwd = self.get_stacks()
        if len(stack) > 1:
            current = stack.pop()  # Remove current
            fwd.append(current)
            previous = stack[-1]
            self.route_to(previous)
    
    def refresh_page(self):
        """Refresh current page"""
        stack, _ = self.get_stacks()
        if stack:
            page = stack[-1]
            self.route_to(page)

    def go_forward(self):
        """Navigate forward"""
        stack, fwd = self.get_stacks()
        if fwd:
            next_page = fwd.pop()
            stack.append(next_page)
            self.route_to(next_page)
    
    def perform_search(self):
        """Perform search"""
        query = self.search_var.get()
        if not query:
            query = ''
        
        # Search movies
        genre = getattr(self, 'genre_var', tk.StringVar(value='All')).get()
        if genre and genre != 'All':
            movies = db.execute_query(
                "SELECT * FROM movies WHERE title LIKE ? AND genres_json LIKE ?",
                (f"%{query}%", f"%{genre}%"), fetch_all=True
            )
        else:
            movies = db.execute_query(
                "SELECT * FROM movies WHERE title LIKE ?",
                (f"%{query}%",), fetch_all=True
            )
        
        if movies:
            self.show_search_results(movies)
        else:
            messagebox.showinfo("No Results", f"No movies found for '{query}'")
    
    def show_search_results(self, movies):
        """Show search results"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        # Title
        title_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(title_frame, text=f"Search Results ({len(movies)} found)", 
                font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(anchor='w')
        
        # Create scrollable frame
        canvas = tk.Canvas(self.main_container, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display movies
        self.create_movie_grid(scrollable_frame, movies)
        
        # Events section
        events = db.execute_query("SELECT * FROM events ORDER BY upload_date DESC", fetch_all=True)
        if events:
            section = tk.Frame(scrollable_frame, bg='#1a1a1a')
            section.pack(fill=tk.BOTH, expand=True)
            tk.Label(section, text="Discover Events", font=('Arial', 20, 'bold'), bg='#1a1a1a', fg='white').pack(anchor='w', padx=20, pady=(10,0))
            self.create_event_grid(section, events[:8])
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

    def edit_employee_popup(self, emp):
        popup = tk.Toplevel(self.root)
        popup.title("Edit Employee")
        popup.geometry("420x380")
        popup.configure(bg='#1a1a1a')
        frm = tk.Frame(popup, bg='#1a1a1a')
        frm.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        def add_field(row, label, var):
            tk.Label(frm, text=label, bg='#1a1a1a', fg='white').grid(row=row, column=0, sticky='w', pady=6)
            tk.Entry(frm, textvariable=var).grid(row=row, column=1, pady=6, padx=10)
        name_var = tk.StringVar(value=emp.get('name',''))
        desg_var = tk.StringVar(value=emp.get('designation',''))
        city_var = tk.StringVar(value=emp.get('city',''))
        theatre_var = tk.StringVar(value=emp.get('theatre',''))
        salary_var = tk.StringVar(value=str(emp.get('salary',0)))
        add_field(0, 'Name', name_var)
        add_field(1, 'Designation', desg_var)
        add_field(2, 'City', city_var)
        add_field(3, 'Theatre', theatre_var)
        add_field(4, 'Salary', salary_var)
        def save():
            try:
                sal = float(salary_var.get())
            except Exception:
                messagebox.showerror("Error", "Salary must be a number")
                return
            db.execute_query(
                "UPDATE employees SET name=?, designation=?, city=?, theatre=?, salary=? WHERE employee_id=?",
                (name_var.get().strip(), desg_var.get().strip(), city_var.get().strip(), theatre_var.get().strip(), sal, emp.get('employee_id'))
            )
            self.show_toast("Employee updated")
            popup.destroy()
            self.refresh_page()
        tk.Button(frm, text="Save", bg='#4CAF50', fg='white', command=save).grid(row=5, column=0, columnspan=2, pady=12)

    def delete_employee(self, employee_id):
        if not employee_id:
            return
        if not messagebox.askyesno("Confirm", "Remove this employee? This action cannot be undone."):
            return
        db.execute_query("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        self.show_toast("Employee removed")
        self.refresh_page()
    
    def show_event_detail(self, event):
        """Delegated event detail page"""
        try:
            from frontend import pages_user
            return pages_user.show_event_detail(self, event)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def add_to_watchlist_event(self, event_id, popup):
        db.execute_query("INSERT INTO watchlist (user_id, event_id) VALUES (?, ?)", (current_user['user_id'], event_id))
        self.show_toast("Added to watchlist")
        popup.destroy()
    
    def remove_from_watchlist_event(self, event_id, popup):
        db.execute_query("DELETE FROM watchlist WHERE user_id = ? AND event_id = ?", (current_user['user_id'], event_id))
        self.show_toast("Removed from watchlist")
        popup.destroy()

    def show_events_page(self):
        """Full events listing page (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_events_page(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")

    def show_city_selection_for_event(self):
        try:
            from frontend import pages_user
            return pages_user.show_city_selection_for_event(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")

    def show_theatre_listing_for_event(self, city):
        """Delegated theatre listing for event"""
        try:
            from frontend import pages_user
            return pages_user.show_theatre_listing_for_event(self, city)
        except Exception:
            messagebox.showerror("Error", "User module not available")

    def get_all_genres(self):
        """Return sorted list of unique genres from movies"""
        genres_set = set()
        rows = db.execute_query("SELECT genres_json FROM movies", fetch_all=True)
        for r in rows:
            try:
                for g in json.loads(r['genres_json']):
                    genres_set.add(g)
            except:
                continue
        return sorted(genres_set)
    
    def get_all_languages(self):
        """Return sorted list of unique languages from movies"""
        langs_set = set()
        rows = db.execute_query("SELECT languages_json FROM movies", fetch_all=True)
        for r in rows:
            try:
                for l in json.loads(r['languages_json']):
                    langs_set.add(l)
            except:
                continue
        return sorted(langs_set)
    
    def show_register_page(self, role):
        """Show registration page"""
        self.clear_container()
        
        center_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        title = "Register as User" if role == 'user' else "Register as Producer/Host"
        tk.Label(center_frame, text=title, font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        form_frame = tk.Frame(center_frame, bg='#2a2a2a', padx=40, pady=40)
        form_frame.pack(pady=20)
        
        fields = ['Name', 'Email', 'Username', 'Password', 'Confirm Password']
        entries = {}
        
        for i, field in enumerate(fields):
            tk.Label(form_frame, text=field, font=('Arial', 11), 
                    bg='#2a2a2a', fg='white').grid(row=i, column=0, sticky='w', pady=5)
            entry = tk.Entry(form_frame, font=('Arial', 11), width=30,
                           show='*' if 'Password' in field else '')
            entry.grid(row=i, column=1, pady=5, padx=10)
            entries[field] = entry
        
        if role == 'producer':
            tk.Label(form_frame, text="Details", font=('Arial', 11), 
                    bg='#2a2a2a', fg='white').grid(row=5, column=0, sticky='w', pady=5)
            details_entry = tk.Text(form_frame, font=('Arial', 11), width=30, height=4)
            details_entry.grid(row=5, column=1, pady=5, padx=10)
            entries['Details'] = details_entry
        
        def attempt_register():
            name = entries['Name'].get()
            email = entries['Email'].get()
            username = entries['Username'].get()
            password = entries['Password'].get()
            confirm_pwd = entries['Confirm Password'].get()
            
            if not all([name, email, username, password, confirm_pwd]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if password != confirm_pwd:
                messagebox.showerror("Error", "Passwords don't match")
                return
            
            # Email and username/password validation
            import re
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                messagebox.showerror("Error", "Enter a valid email address")
                return
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
                messagebox.showerror("Error", "Username must be 3-20 chars (letters, numbers, underscore)")
                return
            if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
                messagebox.showerror("Error", "Password must be at least 6 chars with letters and numbers")
                return
            
            # Check if username exists
            existing = db.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,), fetch_one=True
            )
            
            if existing:
                messagebox.showerror("Error", "Username already taken")
                return
            
            # Insert user
            user_id = db.execute_query(
                "INSERT INTO users (username, password, role, name, email, balance) VALUES (?, ?, ?, ?, ?, 0)",
                (username, password, role, name, email)
            )
            
            # If producer, create producer entry
            if role == 'producer':
                details = entries['Details'].get('1.0', tk.END).strip() if 'Details' in entries else ''
                db.execute_query(
                    "INSERT INTO producers (user_id, name, details) VALUES (?, ?, ?)",
                    (user_id, name, details)
                )
            
            messagebox.showinfo("Success", "Registration successful! Please login.")
            # Update credentials file
            try:
                self.export_credentials_to_file()
            except Exception:
                pass
            self.show_login_page()
        
        tk.Button(form_frame, text="Register", font=('Arial', 12, 'bold'), 
                 bg='#4CAF50', fg='white', width=15, 
                 command=attempt_register).grid(row=6 if role == 'producer' else 5, 
                                               column=0, columnspan=2, pady=20)
        
        tk.Button(center_frame, text="← Back to Login", font=('Arial', 10), 
                 bg='#555', fg='white', command=self.show_login_page).pack(pady=10)
    
    # ==================== USER PAGES ====================
    
    def show_user_home(self):
        """Show user homepage (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_user_home(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def _load_asset_image(self, rel_path, size):
        """Delegates image loading to frontend.assets with GC-safe cache"""
        if ui_assets:
            try:
                return ui_assets.load_asset_image(rel_path, size, self.image_cache)
            except Exception:
                return None
        return None

    def create_movie_grid(self, parent, movies):
        """Create grid of movie cards"""
        grid_frame = tk.Frame(parent, bg='#1a1a1a')
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Deduplicate by movie_id to avoid repeated cards
        movies_unique = []
        seen_movies = set()
        for m in (movies or []):
            title_key = None
            try:
                title_key = (m.get('title') or '').strip().lower()
            except Exception:
                title_key = None
            mid = m.get('movie_id') if isinstance(m, dict) else None
            key = title_key or mid
            if key in seen_movies:
                continue
            seen_movies.add(key)
            movies_unique.append(m)

        for idx, movie in enumerate(movies_unique):
            row = idx // 4
            col = idx % 4
            
            # Movie card
            card = tk.Frame(grid_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Image
            img_frame = tk.Frame(card, bg='#444', width=180, height=240)
            img_frame.pack(pady=10)
            img_frame.pack_propagate(False)
            cover = movie.get('cover_image_path') or f"assets/{movie['title'].lower().replace(' ', '_').replace(':','')}.jpg"
            photo = self._load_asset_image(cover, (180, 240))
            if photo:
                img_lbl = tk.Label(img_frame, image=photo, bg='#444')
                img_lbl.pack(expand=True)
            else:
                img_lbl = tk.Label(img_frame, text="🎬", font=('Arial', 40), bg='#444', fg='white')
                img_lbl.pack(expand=True)
            
            # Movie info
            title_lbl = tk.Label(card, text=movie['title'], font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white', wraplength=180)
            title_lbl.pack(pady=5)
            
            # Rating
            rating_text = f"⭐ {movie['average_rating']}/5.0"
            tk.Label(card, text=rating_text, font=('Arial', 10), 
                    bg='#2a2a2a', fg='#FFD700').pack()
            
            # Genres
            try:
                genres = json.loads(movie.get('genres_json') or '[]')
                if genres:
                    tk.Label(card, text=', '.join(genres[:2]), font=('Arial', 9), 
                            bg='#2a2a2a', fg='#bbb').pack()
            except Exception:
                pass

            # Languages
            try:
                languages = json.loads(movie['languages_json'])
                lang_text = ', '.join(languages[:2])
                tk.Label(card, text=lang_text, font=('Arial', 9), 
                        bg='#2a2a2a', fg='#888').pack()
            except:
                pass
            
            # Click handlers
            def open_movie(m=movie):
                self.show_movie_detail(m)
            for w in (card, img_frame, img_lbl, title_lbl):
                w.bind("<Button-1>", lambda e, mm=movie: open_movie(mm))
                try:
                    w.config(cursor="hand2")
                except Exception:
                    pass
            tk.Button(card, text="Book Tickets", bg='#4CAF50', fg='white', 
                     font=('Arial', 10, 'bold'), command=lambda m=movie: self.show_movie_detail(m)).pack(pady=10)
        
        # Configure grid columns
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
    
    def create_event_grid(self, parent, events):
        """Create grid of event cards"""
        grid_frame = tk.Frame(parent, bg='#1a1a1a')
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Deduplicate by event_id to avoid repeated cards
        events_unique = []
        seen_events = set()
        for e in (events or []):
            title_key = None
            try:
                title_key = (e.get('title') or '').strip().lower()
            except Exception:
                title_key = None
            eid = e.get('event_id') if isinstance(e, dict) else None
            key = title_key or eid
            if key in seen_events:
                continue
            seen_events.add(key)
            events_unique.append(e)

        for idx, event in enumerate(events_unique):
            row = idx // 4
            col = idx % 4
            card = tk.Frame(grid_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            img_frame = tk.Frame(card, bg='#444', width=180, height=180)
            img_frame.pack(pady=10)
            img_frame.pack_propagate(False)
            cover = event.get('cover_image_path') or f"assets/{event['title'].lower().replace(' ', '_').replace(':','')}.jpg"
            photo = self._load_asset_image(cover, (180, 180))
            if photo:
                img_lbl = tk.Label(img_frame, image=photo, bg='#444')
                img_lbl.pack(expand=True)
            else:
                img_lbl = tk.Label(img_frame, text="🎭", font=('Arial', 40), bg='#444', fg='white')
                img_lbl.pack(expand=True)
            title_lbl = tk.Label(card, text=event['title'], font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white', wraplength=180)
            title_lbl.pack(pady=5)
            rating_text = f"⭐ {event.get('average_rating', 0)}/5.0"
            tk.Label(card, text=rating_text, font=('Arial', 10), bg='#2a2a2a', fg='#FFD700').pack()
            try:
                genres = json.loads(event.get('genres_json') or '[]')
                tk.Label(card, text=', '.join(genres[:2]), font=('Arial', 9), bg='#2a2a2a', fg='#888').pack()
            except:
                pass
            def open_event(e=event):
                self.show_event_detail(e)
            for w in (card, img_frame, img_lbl, title_lbl):
                w.bind("<Button-1>", lambda ev, ee=event: open_event(ee))
                try:
                    w.config(cursor="hand2")
                except Exception:
                    pass
            tk.Button(card, text="Book Tickets", bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), command=lambda e=event: self.show_event_detail(e)).pack(pady=10)
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
    
    def show_movie_detail(self, movie):
        """Delegated movie detail page"""
        try:
            from frontend import pages_user
            return pages_user.show_movie_detail(self, movie)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def add_to_watchlist(self, movie_id, popup):
        """Add movie to watchlist"""
        db.execute_query(
            "INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)",
            (current_user['user_id'], movie_id)
        )
        messagebox.showinfo("Success", "Added to watchlist!")
        popup.destroy()
    
    def remove_from_watchlist(self, movie_id, popup):
        """Remove movie from watchlist"""
        db.execute_query(
            "DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (current_user['user_id'], movie_id)
        )
        messagebox.showinfo("Success", "Removed from watchlist!")
        popup.destroy()
    
    def remove_from_watchlist_page(self, movie_id):
        """Remove from watchlist when invoked from watchlist page and refresh"""
        db.execute_query(
            "DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (current_user['user_id'], movie_id)
        )
        self.show_toast("Removed from watchlist")
        self.refresh_page()

    def get_current_user(self):
        """Return the currently logged-in user dict"""
        return current_user

    def add_balance(self, amount):
        """Add balance to current user's wallet and refresh wallet page"""
        try:
            amount = float(amount)
        except Exception:
            messagebox.showerror("Error", "Enter a valid amount")
            return
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than 0")
            return
        new_balance = (current_user.get('balance', 0) or 0) + amount
        db.execute_query("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, current_user['user_id']))
        current_user['balance'] = new_balance
        self.show_toast(f"Added ₹{int(amount)} to wallet")
        self.refresh_page()

    def show_city_selection(self):
        """Delegated city selection for movies"""
        try:
            from frontend import pages_user
            return pages_user.show_city_selection(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def show_theatre_listing(self, city):
        """Delegated theatre listing for movies"""
        try:
            from frontend import pages_user
            return pages_user.show_theatre_listing(self, city)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def show_seat_selection(self, screen_data):
        """Delegated seat selection UI"""
        try:
            from frontend import pages_user
            return pages_user.show_seat_selection(self, screen_data)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def toggle_seat(self, button, seat_num, price):
        """Toggle seat selection"""
        if seat_num in self.selected_seats:
            # Deselect
            self.selected_seats.remove(seat_num)
            button.config(bg='white', fg='black')
        else:
            # Select
            self.selected_seats.append(seat_num)
            button.config(bg='#4CAF50', fg='white')
        
        # Update total
        total = sum(price for _, price in [(s, p) for s, p in zip(self.selected_seats, [price] * len(self.selected_seats))])
        
        # Recalculate properly
        query = """
            SELECT price_economy, price_central, price_premium 
            FROM scheduled_screens WHERE screen_id = ?
        """
        screen = db.execute_query(query, (self.current_screen_id,), fetch_one=True)
        
        total = 0
        for seat in self.selected_seats:
            row = seat[0]
            if row in ['J', 'I', 'H']:
                total += screen['price_premium']
            elif row in ['G', 'F', 'E', 'D']:
                total += screen['price_central']
            else:
                total += screen['price_economy']
        
        self.total_label.config(text=f"Total: ₹{total}")
    
    def process_payment(self, screen_data):
        """Process payment and create booking"""
        if not self.selected_seats:
            messagebox.showerror("Error", "Please select at least one seat")
            return
        
        # Calculate total
        query = """
            SELECT price_economy, price_central, price_premium 
            FROM scheduled_screens WHERE screen_id = ?
        """
        screen = db.execute_query(query, (self.current_screen_id,), fetch_one=True)
        
        total = 0
        for seat in self.selected_seats:
            row = seat[0]
            if row in ['J', 'I', 'H']:
                total += screen['price_premium']
            elif row in ['G', 'F', 'E', 'D']:
                total += screen['price_central']
            else:
                total += screen['price_economy']
        
        # Check balance
        user = db.execute_query(
            "SELECT balance FROM users WHERE user_id = ?",
            (current_user['user_id'],), fetch_one=True
        )
        
        if user['balance'] < total:
            messagebox.showerror("Insufficient Balance", 
                               "Can't book, you're broke.\n\nPlease add balance to your wallet.")
            return
        
        # Deduct balance
        new_balance = user['balance'] - total
        db.execute_query(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, current_user['user_id'])
        )
        
        # Update global user
        current_user['balance'] = new_balance
        
        # Create bookings and update seat map
        screen_query = "SELECT seat_map_json FROM scheduled_screens WHERE screen_id = ?"
        screen_rec = db.execute_query(screen_query, (self.current_screen_id,), fetch_one=True)
        
        try:
            seat_map = json.loads(screen_rec['seat_map_json'])
        except:
            seat_map = [[0 for _ in range(10)] for _ in range(10)]
        
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        
        for seat in self.selected_seats:
            row_letter = seat[0]
            col_num = int(seat[1:])
            row_idx = 9 - rows.index(row_letter)  # Reverse for display
            col_idx = col_num - 1
            
            # Mark as booked
            seat_map[row_idx][col_idx] = 1
            
            # Determine price
            if row_letter in ['J', 'I', 'H']:
                amount = screen['price_premium']
            elif row_letter in ['G', 'F', 'E', 'D']:
                amount = screen['price_central']
            else:
                amount = screen['price_economy']
            
            # Create booking
            db.execute_query(
                """INSERT INTO bookings (user_id, screen_id, seat, amount, status, booking_date)
                   VALUES (?, ?, ?, ?, 'confirmed', ?)""",
                (current_user['user_id'], self.current_screen_id, seat, float(amount), datetime.now().isoformat())
            )
        
        # Update seat map in DB
        db.execute_query("UPDATE scheduled_screens SET seat_map_json = ? WHERE screen_id = ?", (json.dumps(seat_map), self.current_screen_id))
        try:
            messagebox.showinfo("Success", "Booking confirmed!")
        except Exception:
            pass
        self.selected_seats = []
        self.route_to('my_bookings')
    
    def show_wallet(self):
        """Show wallet page (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_wallet(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def add_balance(self, amount):
        """Add balance to wallet"""
        if amount <= 0:
            messagebox.showerror("Error", "Please enter a valid amount")
            return
        
        new_balance = current_user['balance'] + amount
        db.execute_query(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, current_user['user_id'])
        )
        
        current_user['balance'] = new_balance
        messagebox.showinfo("Success", f"₹{amount} added to wallet!")
        self.refresh_page()
    
    def show_watchlist(self):
        """Show watchlist (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_watchlist(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def remove_from_watchlist_page(self, movie_id):
        """Remove from watchlist and refresh"""
        db.execute_query(
            "DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (current_user['user_id'], movie_id)
        )
        self.refresh_page()
    
    def show_user_profile(self):
        """Show user profile with update options"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="👤 My Profile", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Profile info
        info_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
        info_frame.pack(fill=tk.X, pady=20, padx=50)
        
        tk.Label(info_frame, text=f"Name: {current_user['name']}", font=('Arial', 14), 
                bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=10)
        tk.Label(info_frame, text=f"Email: {current_user['email']}", font=('Arial', 14), 
                bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=10)
        tk.Label(info_frame, text=f"Username: {current_user['username']}", font=('Arial', 14), 
                bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=10)
        tk.Label(info_frame, text=f"Role: {current_user['role'].capitalize()}", font=('Arial', 14), 
                bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=10)
        
        # Action buttons
        btn_frame = tk.Frame(content_frame, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Update Username", bg='#2196F3', fg='white',
                 font=('Arial', 12), width=20, command=self.update_username_popup).pack(pady=5)
        tk.Button(btn_frame, text="Update Password", bg='#2196F3', fg='white',
                 font=('Arial', 12), width=20, command=self.update_password_popup).pack(pady=5)
    
    def update_username_popup(self):
        """Show update username popup"""
        popup = tk.Toplevel(self.root)
        popup.title("Update Username")
        popup.geometry("400x200")
        popup.configure(bg='#1a1a1a')
        
        tk.Label(popup, text="Update Username", font=('Arial', 16, 'bold'), 
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        tk.Label(popup, text="New Username:", font=('Arial', 12), 
                bg='#1a1a1a', fg='white').pack()
        
        username_var = tk.StringVar()
        tk.Entry(popup, textvariable=username_var, font=('Arial', 12), width=30).pack(pady=10)
        
        def update():
            new_username = username_var.get()
            if not new_username:
                messagebox.showerror("Error", "Please enter a username")
                return
            
            # Check if exists
            existing = db.execute_query(
                "SELECT * FROM users WHERE username = ? AND user_id != ?",
                (new_username, current_user['user_id']), fetch_one=True
            )
            
            if existing:
                messagebox.showerror("Error", "Username already taken")
                return
            
            # Update
            db.execute_query(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (new_username, current_user['user_id'])
            )
            
            current_user['username'] = new_username
            messagebox.showinfo("Success", "Username updated successfully!")
            popup.destroy()
            self.refresh_page()
        
        tk.Button(popup, text="Update", bg='#4CAF50', fg='white',
                 font=('Arial', 12), command=update).pack(pady=10)
    
    def update_password_popup(self):
        """Show update password popup"""
        popup = tk.Toplevel(self.root)
        popup.title("Update Password")
        popup.geometry("400x300")
        popup.configure(bg='#1a1a1a')
        
        tk.Label(popup, text="Update Password", font=('Arial', 16, 'bold'), 
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Old password
        tk.Label(popup, text="Old Password:", font=('Arial', 11), 
                bg='#1a1a1a', fg='white').pack()
        old_pass_var = tk.StringVar()
        tk.Entry(popup, textvariable=old_pass_var, font=('Arial', 11), width=30, show='*').pack(pady=5)
        
        # New password
        tk.Label(popup, text="New Password:", font=('Arial', 11), 
                bg='#1a1a1a', fg='white').pack()
        new_pass_var = tk.StringVar()
        tk.Entry(popup, textvariable=new_pass_var, font=('Arial', 11), width=30, show='*').pack(pady=5)
        
        # Confirm password
        tk.Label(popup, text="Confirm New Password:", font=('Arial', 11), 
                bg='#1a1a1a', fg='white').pack()
        confirm_pass_var = tk.StringVar()
        tk.Entry(popup, textvariable=confirm_pass_var, font=('Arial', 11), width=30, show='*').pack(pady=5)
        
        def update():
            old_pass = old_pass_var.get()
            new_pass = new_pass_var.get()
            confirm_pass = confirm_pass_var.get()
            
            if not all([old_pass, new_pass, confirm_pass]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if old_pass != current_user['password']:
                messagebox.showerror("Error", "Old password is incorrect")
                return
            
            if new_pass == old_pass:
                messagebox.showerror("Error", "New password must be different from old password")
                return
            
            if new_pass != confirm_pass:
                messagebox.showerror("Error", "New passwords don't match")
                return
            
            # Update
            db.execute_query(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (new_pass, current_user['user_id'])
            )
            
            current_user['password'] = new_pass
            messagebox.showinfo("Success", "Password updated successfully!")
            popup.destroy()
        
        tk.Button(popup, text="Update", bg='#4CAF50', fg='white',
                 font=('Arial', 12), command=update).pack(pady=15)
    
    def show_my_bookings(self):
        """Show upcoming bookings (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_my_bookings(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def show_booking_history(self):
        """Show all booking history (delegated)"""
        try:
            from frontend import pages_user
            return pages_user.show_booking_history(self)
        except Exception:
            messagebox.showerror("Error", "User module not available")
    
    def show_feedback_form(self):
        """Show feedback form"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="📝 Send Feedback", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        tk.Label(content_frame, text="We value your feedback!", font=('Arial', 12), 
                bg='#1a1a1a', fg='#888').pack()
        
        # Feedback text area
        feedback_text = scrolledtext.ScrolledText(content_frame, font=('Arial', 12), 
                                                   width=60, height=15, wrap=tk.WORD)
        feedback_text.pack(pady=20)
        
        def submit_feedback():
            text = feedback_text.get('1.0', tk.END).strip()
            if not text:
                messagebox.showerror("Error", "Please enter your feedback")
                return
            
            db.execute_query(
                """INSERT INTO feedbacks (user_id, text, timestamp, read_flag)
                   VALUES (?, ?, ?, 0)""",
                (current_user['user_id'], text, datetime.now().isoformat())
            )
            
            messagebox.showinfo("Success", "Thank you for your feedback!")
            feedback_text.delete('1.0', tk.END)
        
        tk.Button(content_frame, text="Submit Feedback", bg='#4CAF50', fg='white',
                 font=('Arial', 14, 'bold'), command=submit_feedback).pack(pady=10)
    
    # ==================== PRODUCER PAGES ====================
    
    def show_producer_dashboard(self):
        """Producer dashboard (delegated)"""
        try:
            from frontend import pages_producer
            return pages_producer.show_producer_dashboard(self)
        except Exception:
            messagebox.showerror("Error", "Producer module not available")
    
    def show_add_content(self):
        """Show add content quick entry (opens movie form)"""
        # Shortcut to open add-movie form
        self.open_movie_form()

    def get_current_producer_id(self):
        """Return producer_id for current user or None"""
        try:
            row = db.execute_query("SELECT producer_id FROM producers WHERE user_id = ?", (current_user['user_id'],), fetch_one=True)
            return row['producer_id'] if row else None
        except:
            return None

    def open_movie_form(self, edit=False, movie=None):
        """Popup for add/edit movie. If edit=True, prefill with movie."""
        producer_id = self.get_current_producer_id()
        if not producer_id:
            messagebox.showerror("Error", "Producer profile not found.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Edit Movie" if edit else "Add Movie")
        popup.geometry("600x700")
        popup.configure(bg='#1a1a1a')

        fields = {}
        form = tk.Frame(popup, bg='#1a1a1a')
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        def add_field(label, var_type='entry', default=''):
            row = tk.Frame(form, bg='#1a1a1a')
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label, bg='#1a1a1a', fg='white', width=16, anchor='w').pack(side=tk.LEFT)
            if var_type == 'text':
                widget = tk.Text(row, height=4, width=40)
                if default:
                    widget.insert('1.0', default)
                widget.pack(side=tk.LEFT)
            else:
                var = tk.StringVar(value=default)
                widget = tk.Entry(row, textvariable=var, width=40)
                widget.pack(side=tk.LEFT)
            fields[label] = widget

        # Prefill defaults from movie if edit
        m = movie or {}
        add_field('Title', default=m.get('title',''))
        add_field('Description', var_type='text', default=m.get('description',''))
        # comma-separated inputs
        actors_default = ''
        if m.get('actors_json'):
            try:
                actors_default = ', '.join(json.loads(m['actors_json']))
            except: pass
        add_field('Actors (comma-separated)', default=actors_default)
        langs_default = ''
        if m.get('languages_json'):
            try:
                langs_default = ', '.join(json.loads(m['languages_json']))
            except: pass
        add_field('Languages (comma-separated)', default=langs_default)
        genres_default = ''
        if m.get('genres_json'):
            try:
                genres_default = ', '.join(json.loads(m['genres_json']))
            except: pass
        add_field('Genres (comma-separated)', default=genres_default)
        # duration in minutes for simplicity
        dur_default = '' if not m.get('duration_seconds') else str(int(m['duration_seconds']//60))
        add_field('Duration (minutes)', default=dur_default)
        add_field('Viewer Rating (e.g., PG-13)', default=m.get('viewer_rating',''))
        add_field('Average Rating (0-5)', default=str(m.get('average_rating','') or ''))
        # optional cover image filename
        cov = m.get('cover_image_path','')
        cover_default = os.path.basename(cov) if cov else ''
        add_field('Cover Filename (optional)', default=cover_default)

        def get_text(widget):
            return widget.get('1.0', tk.END).strip()

        def get_entry(widget):
            if isinstance(widget, tk.Entry):
                return widget.get().strip()
            # If Text accidentally, fallback
            try:
                return get_text(widget)
            except:
                return ''

        def on_save():
            title = get_entry(fields['Title'])
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            # pull existing when editing and field left blank
            def fallback(key, value):
                return value if value else (m.get(key) if edit else '')

            description = fallback('description', get_text(fields['Description']))
            actors = fallback('actors_json', get_entry(fields['Actors (comma-separated)']))
            languages = fallback('languages_json', get_entry(fields['Languages (comma-separated)']))
            genres = fallback('genres_json', get_entry(fields['Genres (comma-separated)']))
            duration_minutes = get_entry(fields['Duration (minutes)'])
            viewer_rating = fallback('viewer_rating', get_entry(fields['Viewer Rating (e.g., PG-13)']))
            avg_rating = get_entry(fields['Average Rating (0-5)'])
            cover_filename = get_entry(fields['Cover Filename (optional)'])

            # conversions
            try:
                duration_seconds = int(duration_minutes) * 60 if duration_minutes else (m.get('duration_seconds') if edit else None)
            except:
                messagebox.showerror("Error", "Duration must be a whole number of minutes")
                return
            try:
                average_rating = float(avg_rating) if avg_rating != '' else (m.get('average_rating') if edit else 0)
            except:
                messagebox.showerror("Error", "Average rating must be a number")
                return
            actors_json = json.dumps([a.strip() for a in actors.split(',') if a.strip()]) if actors != '' else (m.get('actors_json') if edit else json.dumps([]))
            languages_json = json.dumps([l.strip() for l in languages.split(',') if l.strip()]) if languages != '' else (m.get('languages_json') if edit else json.dumps([]))
            genres_json = json.dumps([g.strip() for g in genres.split(',') if g.strip()]) if genres != '' else (m.get('genres_json') if edit else json.dumps([]))

            if cover_filename:
                cover_image_path = f"assets/{cover_filename}"
            else:
                # generate expected filename and log requirement
                auto_name = f"{title.lower().replace(' ', '_').replace(':','')}" + ".jpg"
                cover_image_path = f"assets/{auto_name}"
                try:
                    req_path = os.path.join(os.path.dirname(__file__), 'provide-these.txt')
                    with open(req_path, 'a') as f:
                        f.write(f"{auto_name} - cover image for movie {title}\n")
                except:
                    pass

            if edit:
                # Ensure only own movie is edited
                db.execute_query(
                    """UPDATE movies SET title=?, description=?, actors_json=?, languages_json=?, duration_seconds=?, viewer_rating=?, cover_image_path=?, genres_json=?, average_rating=? WHERE movie_id=? AND producer_id=?""",
                    (title, description, actors_json, languages_json, duration_seconds, viewer_rating, cover_image_path, genres_json, average_rating, m['movie_id'], producer_id)
                )
            else:
                db.execute_query(
                    """INSERT INTO movies (producer_id, title, description, actors_json, languages_json, duration_seconds, viewer_rating, cover_image_path, genres_json, average_rating, upload_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (producer_id, title, description, actors_json, languages_json, duration_seconds or 0, viewer_rating, cover_image_path, genres_json, average_rating, datetime.now().isoformat())
                )
            self.show_toast("Movie saved")
            popup.destroy()
            self.refresh_page()

        # Add Save button (missing earlier)
        tk.Button(form, text="Save", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=on_save).pack(pady=12)

    def open_event_form(self, edit=False, event=None):
        """Popup for add/edit event. If edit=True, prefill with event."""
        producer_id = self.get_current_producer_id()
        if not producer_id:
            messagebox.showerror("Error", "Producer profile not found.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Edit Event" if edit else "Add Event")
        popup.geometry("600x720")
        popup.configure(bg='#1a1a1a')

        fields = {}
        form = tk.Frame(popup, bg='#1a1a1a')
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        def add_field(label, var_type='entry', default=''):
            row = tk.Frame(form, bg='#1a1a1a')
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label, bg='#1a1a1a', fg='white', width=20, anchor='w').pack(side=tk.LEFT)
            if var_type == 'text':
                widget = tk.Text(row, height=4, width=40)
                if default:
                    widget.insert('1.0', default)
                widget.pack(side=tk.LEFT)
            else:
                var = tk.StringVar(value=default)
                widget = tk.Entry(row, textvariable=var, width=40)
                widget.pack(side=tk.LEFT)
            fields[label] = widget

        e = event or {}
        add_field('Title', default=e.get('title',''))
        add_field('Description', var_type='text', default=e.get('description',''))
        performers_default = ''
        if e.get('performers_json'):
            try:
                performers_default = ', '.join(json.loads(e['performers_json']))
            except: pass
        add_field('Performers (comma-separated)', default=performers_default)
        add_field('Venue', default=e.get('venue',''))
        dur_default = '' if not e.get('duration_seconds') else str(int(e['duration_seconds']//60))
        add_field('Duration (minutes)', default=dur_default)
        add_field('Average Rating (0-5)', default=str(e.get('average_rating','') or ''))
        genres_default = ''
        if e.get('genres_json'):
            try:
                genres_default = ', '.join(json.loads(e['genres_json']))
            except: pass
        add_field('Genres (comma-separated)', default=genres_default)
        cov = e.get('cover_image_path','')
        cover_default = os.path.basename(cov) if cov else ''
        add_field('Cover Filename (optional)', default=cover_default)

        def get_text(widget):
            return widget.get('1.0', tk.END).strip()

        def get_entry(widget):
            if isinstance(widget, tk.Entry):
                return widget.get().strip()
            try:
                return get_text(widget)
            except:
                return ''

        def on_save():
            title = get_entry(fields['Title'])
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            description = get_text(fields['Description']) if get_text else e.get('description','')
            performers = get_entry(fields['Performers (comma-separated)'])
            venue = get_entry(fields['Venue'])
            duration_minutes = get_entry(fields['Duration (minutes)'])
            avg_rating = get_entry(fields['Average Rating (0-5)'])
            genres = get_entry(fields['Genres (comma-separated)'])
            cover_filename = get_entry(fields['Cover Filename (optional)'])

            try:
                duration_seconds = int(duration_minutes) * 60 if duration_minutes else (e.get('duration_seconds') if edit else None)
            except:
                messagebox.showerror("Error", "Duration must be a whole number of minutes")
                return
            try:
                average_rating = float(avg_rating) if avg_rating != '' else (e.get('average_rating') if edit else 0)
            except:
                messagebox.showerror("Error", "Average rating must be a number")
                return
            performers_json = json.dumps([p.strip() for p in performers.split(',') if p.strip()]) if performers != '' else (e.get('performers_json') if edit else json.dumps([]))
            genres_json = json.dumps([g.strip() for g in genres.split(',') if g.strip()]) if genres != '' else (e.get('genres_json') if edit else json.dumps([]))

            if cover_filename:
                cover_image_path = f"assets/{cover_filename}"
            else:
                auto_name = f"{title.lower().replace(' ', '_').replace(':','')}" + ".jpg"
                cover_image_path = f"assets/{auto_name}"
                try:
                    req_path = os.path.join(os.path.dirname(__file__), 'provide-these.txt')
                    with open(req_path, 'a') as f:
                        f.write(f"{auto_name} - cover image for event {title}\n")
                except:
                    pass

            if edit:
                db.execute_query(
                    """UPDATE events SET title=?, description=?, performers_json=?, venue=?, duration_seconds=?, average_rating=?, cover_image_path=?, genres_json=? WHERE event_id=? AND host_id=?""",
                    (title, description, performers_json, venue, duration_seconds, average_rating, cover_image_path, genres_json, e['event_id'], producer_id)
                )
            else:
                db.execute_query(
                    """INSERT INTO events (host_id, title, description, performers_json, venue, duration_seconds, average_rating, cover_image_path, genres_json, upload_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (producer_id, title, description, performers_json, venue, duration_seconds or 0, average_rating, cover_image_path, genres_json, datetime.now().isoformat())
                )
            self.show_toast("Event saved")
            popup.destroy()
            self.refresh_page()

        tk.Button(form, text="Save", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=on_save).pack(pady=12)

    def delete_event(self, event_id):
        """Delete an event owned by current producer"""
        if not messagebox.askyesno("Confirm", "Delete this event? This cannot be undone."):
            return
        producer_id = self.get_current_producer_id()
        if not producer_id:
            return
        db.execute_query("DELETE FROM events WHERE event_id = ? AND host_id = ?", (event_id, producer_id))
        self.show_toast("Event deleted")
        self.refresh_page()

    def show_producer_analytics(self):
        """Analytics for the logged-in producer (delegated)"""
        try:
            from frontend import pages_producer
            return pages_producer.show_producer_analytics(self)
        except Exception:
            messagebox.showerror("Error", "Producer module not available")

    def show_admin_analytics(self):
        """Admin analytics with bar, line, donut, semi-donut charts"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)

        if not FigureCanvasTkAgg or not plt:
            frame = tk.Frame(self.main_container, bg='#1a1a1a')
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            tk.Label(frame, text="Matplotlib not available. Please install matplotlib to view analytics.",
                    bg='#1a1a1a', fg='white', font=('Arial', 14)).pack(pady=20)
            return

        content = tk.Frame(self.main_container, bg='#1a1a1a')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Fetch data
        sales = db.execute_query(
            """
            SELECT m.title, SUM(b.amount) AS total, COUNT(b.booking_id) AS cnt
            FROM bookings b
            JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
            JOIN movies m ON ss.movie_id = m.movie_id
            GROUP BY m.title
            ORDER BY total DESC
            """, fetch_all=True)

        # Daily trends for last 14 days
        trends = db.execute_query(
            """
            SELECT DATE(booking_date) as d, COUNT(*) as c
            FROM bookings
            WHERE DATE(booking_date) >= DATE('now', '-14 day')
            GROUP BY DATE(booking_date)
            ORDER BY d
            """, fetch_all=True)

        # Genre distribution
        genres_rows = db.execute_query("SELECT genres_json FROM movies", fetch_all=True)
        genre_counts = {}
        for r in genres_rows:
            try:
                for g in json.loads(r['genres_json']):
                    genre_counts[g] = genre_counts.get(g, 0) + 1
            except:
                pass

        # Occupancy percentage (booked seats / total seats in next 3 days)
        screens = db.execute_query(
            """
            SELECT seat_map_json FROM scheduled_screens
            WHERE DATE(start_time) >= DATE('now') AND DATE(start_time) <= DATE('now', '+3 day')
            """, fetch_all=True)
        total_seats = len(screens) * 100
        booked = 0
        for s in screens:
            try:
                seat_map = json.loads(s['seat_map_json'])
                booked += sum(row.count(1) for row in seat_map)
            except:
                pass
        occupancy = (booked / total_seats) * 100 if total_seats else 0

        # Layout frames
        top = tk.Frame(content, bg='#1a1a1a')
        bottom = tk.Frame(content, bg='#1a1a1a')
        top.pack(fill=tk.BOTH, expand=True)
        bottom.pack(fill=tk.BOTH, expand=True)

        def add_chart(parent, fig):
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Bar: ticket sales per movie
        fig1, ax1 = plt.subplots(figsize=(5,3))
        if sales:
            titles = [row['title'] for row in sales][:10]
            totals = [row['total'] or 0 for row in sales][:10]
            ax1.bar(titles, totals, color='#4CAF50')
            ax1.set_title('Ticket Sales per Movie')
            ax1.tick_params(axis='x', labelrotation=45)
        else:
            ax1.text(0.5,0.5,'No data', ha='center')
        add_chart(top, fig1)

        # Line: daily bookings trend
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

        # Donut: genre distribution
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

        # Semicircular donut: occupancy percentage
        fig4, ax4 = plt.subplots(figsize=(5,3), subplot_kw=dict(aspect="equal"))
        # Two segments: occupied vs free; only half circle
        occupied = max(0, min(100, occupancy))
        free = 100 - occupied
        # Create a full donut but mask to semicircle by setting ylim
        wedges, _ = ax4.pie([occupied, free], startangle=180, counterclock=False, colors=['#FF9800', '#EEEEEE'], wedgeprops=dict(width=0.4))
        ax4.set_title(f'Average Occupancy: {occupied:.1f}%')
        ax4.set_ylim(-1, 0.1)  # show top half
        add_chart(bottom, fig4)

    def delete_movie(self, movie_id):
        """Delete a movie owned by current producer"""
        if not messagebox.askyesno("Confirm", "Delete this movie? This cannot be undone."):
            return
        producer_id = self.get_current_producer_id()
        if not producer_id:
            return
        db.execute_query("DELETE FROM movies WHERE movie_id = ? AND producer_id = ?", (movie_id, producer_id))
        self.show_toast("Movie deleted")
        self.refresh_page()

    def _refund_and_delete_screen(self, screen_id):
        bookings = db.execute_query("SELECT * FROM bookings WHERE screen_id = ? AND status = 'confirmed'", (screen_id,), fetch_all=True)
        for b in (bookings or []):
            user = db.execute_query("SELECT balance FROM users WHERE user_id = ?", (b['user_id'],), fetch_one=True)
            new_bal = (user['balance'] or 0) + (b['amount'] or 0)
            db.execute_query("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, b['user_id']))
            db.execute_query("UPDATE bookings SET status = 'cancelled', refunded_flag = 1 WHERE booking_id = ?", (b['booking_id'],))
        db.execute_query("DELETE FROM scheduled_screens WHERE screen_id = ?", (screen_id,))

    def admin_delete_show(self, screen_id):
        if not messagebox.askyesno("Confirm", "Delete this show and refund all bookings? This cannot be undone."):
            return
        self._refund_and_delete_screen(screen_id)
        self.show_toast("Show deleted and bookings refunded")
        self.refresh_page()

    def admin_delete_movie(self, movie_id):
        if not messagebox.askyesno("Confirm", "Delete this movie, unschedule all its shows, and refund all bookings? This cannot be undone."):
            return
        # show a lightweight progress window
        self._progress_window = tk.Toplevel(self.root)
        self._progress_window.title("Processing...")
        self._progress_window.geometry("300x120")
        self._progress_window.configure(bg='#1a1a1a')
        tk.Label(self._progress_window, text="Deleting movie...\nPlease wait", bg='#1a1a1a', fg='white').pack(expand=True, fill=tk.BOTH, padx=12, pady=12)
        self._progress_window.transient(self.root)
        self._progress_window.grab_set()
        self.root.update_idletasks()
        # run heavy DB work off the UI thread
        threading.Thread(target=self._admin_delete_movie_worker, args=(movie_id,), daemon=True).start()

    def _admin_delete_movie_worker(self, movie_id):
        """Background thread worker: refund bookings for all screens of the movie and delete the movie.
        Only performs DB operations. No Tk calls here.
        """
        try:
            screens = db.execute_query("SELECT screen_id FROM scheduled_screens WHERE movie_id = ?", (movie_id,), fetch_all=True)
            for s in (screens or []):
                self._refund_and_delete_screen(s['screen_id'])
            db.execute_query("DELETE FROM movies WHERE movie_id = ?", (movie_id,))
            # signal success back on main thread
            self.root.after(0, lambda: self._on_admin_delete_movie_done(success=True))
        except Exception:
            self.root.after(0, lambda: self._on_admin_delete_movie_done(success=False))

    def _on_admin_delete_movie_done(self, success):
        """Runs on main thread after background deletion completes."""
        try:
            if hasattr(self, '_progress_window') and self._progress_window and self._progress_window.winfo_exists():
                self._progress_window.destroy()
        except Exception:
            pass
        if success:
            self.show_toast("Movie deleted, shows unscheduled, bookings refunded")
            self.refresh_page()
        else:
            messagebox.showerror("Error", "Failed to delete movie. Please try again.")

    def admin_delete_event(self, event_id):
        if not messagebox.askyesno("Confirm", "Delete this event, unschedule all its shows, and refund all bookings? This cannot be undone."):
            return
        screens = db.execute_query("SELECT screen_id FROM scheduled_screens WHERE event_id = ?", (event_id,), fetch_all=True)
        for s in (screens or []):
            self._refund_and_delete_screen(s['screen_id'])
        db.execute_query("DELETE FROM events WHERE event_id = ?", (event_id,))
        self.show_toast("Event deleted, shows unscheduled, bookings refunded")
        self.refresh_page()

    # ==================== ADMIN PAGES ====================
    
    def show_admin_profile(self):
        """Show admin dashboard"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_search=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Admin Dashboard", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Stats
        stats_frame = tk.Frame(content_frame, bg='#1a1a1a')
        stats_frame.pack(fill=tk.X, pady=20)
        
        # Total users
        users_count = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role='user'", fetch_one=True)
        movies_count = db.execute_query("SELECT COUNT(*) as count FROM movies", fetch_one=True)
        bookings_count = db.execute_query("SELECT COUNT(*) as count FROM bookings", fetch_one=True)
        revenue = db.execute_query("SELECT SUM(amount) as total FROM bookings", fetch_one=True)
        
        stats = [
            ("👥 Total Users", users_count['count']),
            ("🎬 Total Movies", movies_count['count']),
            ("🎫 Total Bookings", bookings_count['count']),
            ("💰 Total Revenue", f"₹{revenue['total'] or 0}")
        ]
        
        for i, (label, value) in enumerate(stats):
            stat_card = tk.Frame(stats_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            stat_card.grid(row=0, column=i, padx=10, pady=10, sticky='nsew')
            
            tk.Label(stat_card, text=label, font=('Arial', 12), 
                    bg='#2a2a2a', fg='#888').pack(pady=10, padx=20)
            tk.Label(stat_card, text=str(value), font=('Arial', 20, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(pady=10, padx=20)
        
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        # Maintenance actions
        actions = tk.Frame(content_frame, bg='#1a1a1a')
        actions.pack(fill=tk.X, pady=10)
        tk.Button(actions, text="Purge Non-Core Data", bg='#d32f2f', fg='white',
                  command=self.purge_non_core_data).pack(side=tk.LEFT, padx=5)
        tk.Button(actions, text="Reset All Passwords", bg='#FF9800', fg='white',
                  command=self.reset_all_passwords).pack(side=tk.LEFT, padx=5)

    def purge_non_core_data(self):
        """Delete all data except movies and theatres; ensure admin snaksartrate/password.
        Keeps producers because movies reference them; cities remain as theatre.city text.
        """
        if not messagebox.askyesno("Confirm", "This will delete all bookings, schedules, events, employees, feedbacks, watchlists, and users (except admin). Continue?"):
            return
        # Delete dependent tables first (FK order)
        try:
            db.execute_query("DELETE FROM bookings")
        except Exception:
            pass
        try:
            db.execute_query("DELETE FROM scheduled_screens")
        except Exception:
            pass
        try:
            db.execute_query("DELETE FROM events")
        except Exception:
            pass
        try:
            db.execute_query("DELETE FROM employees")
        except Exception:
            pass
        try:
            db.execute_query("DELETE FROM feedbacks")
        except Exception:
            pass
        try:
            db.execute_query("DELETE FROM watchlist")
        except Exception:
            pass
        # Reset admin and remove other users
        existing = db.execute_query("SELECT user_id FROM users WHERE username = ?", ("snaksartrate",), fetch_one=True)
        if existing:
            db.execute_query("UPDATE users SET password='password', role='admin', name='Administrator', email='admin@example.com', balance=0 WHERE username='snaksartrate'")
        else:
            db.execute_query(
                "INSERT INTO users (username, password, role, name, email, balance) VALUES (?, ?, 'admin', ?, ?, 0)",
                ("snaksartrate", "password", "Administrator", "admin@example.com")
            )
        # Remove all users except the admin
        db.execute_query("DELETE FROM users WHERE username <> 'snaksartrate'")
        self.show_toast("Non-core data purged; admin reset to snaksartrate/password")
        # Refresh any pages relying on counts
        self.refresh_page()
    
    def show_cinema_halls(self):
        """Show cinema halls management"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="🎬 Cinema Halls Management", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=(10,12))
        
        # Top actions
        actions = tk.Frame(content_frame, bg='#1a1a1a')
        actions.pack(fill=tk.X)
        tk.Button(actions, text="➕ Add Theatre", bg='#4CAF50', fg='white', command=lambda: self.open_theatre_form()).pack(side=tk.LEFT)
        
        # Get all theatres
        theatres = db.execute_query("SELECT * FROM theatres ORDER BY city, name", fetch_all=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Group by city
        cities = {}
        for theatre in theatres:
            if theatre['city'] not in cities:
                cities[theatre['city']] = []
            cities[theatre['city']].append(theatre)
        
        # Display by city (each city has its own horizontally scrollable table)
        for city, city_theatres in cities.items():
            city_frame = tk.Frame(scrollable_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            city_frame.pack(fill=tk.X, padx=10, pady=10)
            tk.Label(city_frame, text=city, font=('Arial', 16, 'bold'), bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=10)

            # Horizontal scrollable table container
            table_container = tk.Frame(city_frame, bg='#2a2a2a'); table_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,10))
            h_canvas = tk.Canvas(table_container, bg='#2a2a2a', highlightthickness=0)
            x_scroll = ttk.Scrollbar(table_container, orient='horizontal', command=h_canvas.xview)
            table_inner = tk.Frame(h_canvas, bg='#2a2a2a')
            table_inner.bind('<Configure>', lambda e, c=h_canvas: c.configure(scrollregion=c.bbox('all')))
            h_canvas.create_window((0,0), window=table_inner, anchor='nw')
            h_canvas.configure(xscrollcommand=x_scroll.set)

            # Build table
            header_bg = '#333'
            cols = ["City", "Theatre", "Hall Type", "3D", "IMAX", "Screens", "Seats/Screen", "Actions"]
            header = tk.Frame(table_inner, bg=header_bg)
            header.grid(row=0, column=0, columnspan=len(cols), sticky='ew')
            for i, col_name in enumerate(cols):
                tk.Label(header, text=col_name, font=('Arial', 11, 'bold'), bg=header_bg, fg='white', padx=12, pady=8).grid(row=0, column=i, sticky='w')
                header.grid_columnconfigure(i, weight=1)

            for r, theatre in enumerate(city_theatres, start=1):
                rowf = tk.Frame(table_inner, bg='#333')
                rowf.grid(row=r, column=0, sticky='ew', pady=2)
                for i in range(len(cols)):
                    rowf.grid_columnconfigure(i, weight=1)

                # Parse schema
                try:
                    schema = json.loads(theatre.get('seating_schema_json') or '{}')
                except Exception:
                    schema = {}
                three_d = 'Yes' if schema.get('3d') else 'No'
                imax = 'Yes' if schema.get('imax') else 'No'
                screens = schema.get('screens', '')
                seats = schema.get('seats_per_screen', '')

                tk.Label(rowf, text=theatre.get('city',''), font=('Arial', 10), bg='#333', fg='white', padx=12, pady=6, anchor='w').grid(row=0, column=0, sticky='ew')
                tk.Label(rowf, text=theatre.get('name',''), font=('Arial', 10), bg='#333', fg='white', padx=12, pady=6, anchor='w').grid(row=0, column=1, sticky='ew')
                tk.Label(rowf, text=theatre.get('hall_type',''), font=('Arial', 10), bg='#333', fg='white', padx=12, pady=6, anchor='w').grid(row=0, column=2, sticky='ew')
                tk.Label(rowf, text=three_d, font=('Arial', 10, 'bold'), bg='#333', fg=('#8BC34A' if three_d=='Yes' else '#FF9800'), padx=12, pady=6, anchor='w').grid(row=0, column=3, sticky='ew')
                tk.Label(rowf, text=imax, font=('Arial', 10, 'bold'), bg='#333', fg=('#8BC34A' if imax=='Yes' else '#FF9800'), padx=12, pady=6, anchor='w').grid(row=0, column=4, sticky='ew')
                tk.Label(rowf, text=str(screens), font=('Arial', 10), bg='#333', fg='white', padx=12, pady=6, anchor='w').grid(row=0, column=5, sticky='ew')
                tk.Label(rowf, text=str(seats), font=('Arial', 10), bg='#333', fg='white', padx=12, pady=6, anchor='w').grid(row=0, column=6, sticky='ew')
                actions = tk.Frame(rowf, bg='#333'); actions.grid(row=0, column=7, sticky='e', padx=8)
                tk.Button(actions, text="Edit", bg='#2196F3', fg='white', width=8, command=lambda th=theatre: self.open_theatre_form(edit=True, theatre=th)).pack(side=tk.LEFT, padx=4)
                tk.Button(actions, text="Delete", bg='#d32f2f', fg='white', width=8, command=lambda tid=theatre['theatre_id']: self.delete_theatre(tid)).pack(side=tk.LEFT, padx=4)

            h_canvas.pack(side='top', fill='both', expand=True)
            x_scroll.pack(side='bottom', fill='x')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def open_theatre_form(self, edit=False, theatre=None):
        popup = tk.Toplevel(self.root)
        popup.title("Edit Theatre" if edit else "Add Theatre")
        popup.geometry("520x420")
        popup.configure(bg='#1a1a1a')
        form = tk.Frame(popup, bg='#1a1a1a')
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        def row(label):
            r = tk.Frame(form, bg='#1a1a1a'); r.pack(fill=tk.X, pady=6)
            tk.Label(r, text=label, bg='#1a1a1a', fg='white', width=16, anchor='w').pack(side=tk.LEFT)
            return r
        th = theatre or {}
        r1 = row('City'); city_var = tk.StringVar(value=th.get('city','')); tk.Entry(r1, textvariable=city_var, width=32).pack(side=tk.LEFT)
        r2 = row('Name'); name_var = tk.StringVar(value=th.get('name','')); tk.Entry(r2, textvariable=name_var, width=32).pack(side=tk.LEFT)
        r3 = row('Hall Type'); hall_var = tk.StringVar(value=th.get('hall_type','cinema')); ttk.Combobox(r3, textvariable=hall_var, values=['cinema','stage'], width=29, state='readonly').pack(side=tk.LEFT)
        # Schema editor (3d, imax, screens, seats)
        try:
            schema = json.loads(th.get('seating_schema_json') or '{}')
        except:
            schema = {}
        r4 = row('3D'); three_d = tk.BooleanVar(value=bool(schema.get('3d'))); ttk.Checkbutton(r4, variable=three_d).pack(side=tk.LEFT)
        r5 = row('IMAX'); imax = tk.BooleanVar(value=bool(schema.get('imax'))); ttk.Checkbutton(r5, variable=imax).pack(side=tk.LEFT)
        r6 = row('Screens'); screens_var = tk.StringVar(value=str(schema.get('screens', 5))); tk.Entry(r6, textvariable=screens_var, width=10).pack(side=tk.LEFT)
        r7 = row('Seats/Screen'); seats_var = tk.StringVar(value=str(schema.get('seats_per_screen', 100))); tk.Entry(r7, textvariable=seats_var, width=10).pack(side=tk.LEFT)
        
        def save():
            city = city_var.get().strip(); name = name_var.get().strip(); hall = hall_var.get().strip()
            if not city or not name or not hall:
                messagebox.showerror("Error", "City, Name and Hall Type are required")
                return
            try:
                screens = int(screens_var.get()); seats = int(seats_var.get())
                if screens <= 0 or seats <= 0:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Screens and Seats must be positive integers")
                return
            schema = json.dumps({'3d': bool(three_d.get()), 'imax': bool(imax.get()), 'screens': screens, 'seats_per_screen': seats})
            if edit:
                db.execute_query("UPDATE theatres SET city=?, name=?, hall_type=?, seating_schema_json=? WHERE theatre_id=?", (city, name, hall, schema, th['theatre_id']))
            else:
                db.execute_query("INSERT INTO theatres (city, name, hall_type, seating_schema_json) VALUES (?, ?, ?, ?)", (city, name, hall, schema))
            self.show_toast("Theatre saved")
            popup.destroy()
            self.refresh_page()
        tk.Button(form, text="Save", bg='#4CAF50', fg='white', command=save).pack(pady=10)
    
    def delete_theatre(self, theatre_id):
        if not messagebox.askyesno("Confirm", "Delete this theatre? This will also remove its schedules and related bookings."):
            return
        # Delete bookings for screens in this theatre
        screens = db.execute_query("SELECT screen_id FROM scheduled_screens WHERE theatre_id = ?", (theatre_id,), fetch_all=True)
        for s in (screens or []):
            db.execute_query("DELETE FROM bookings WHERE screen_id = ?", (s['screen_id'],))
        db.execute_query("DELETE FROM scheduled_screens WHERE theatre_id = ?", (theatre_id,))
        db.execute_query("DELETE FROM theatres WHERE theatre_id = ?", (theatre_id,))
        self.show_toast("Theatre deleted")
        self.refresh_page()
    
    def show_employees(self):
        """Show employees management"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="👥 Employee Management", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=(10,12))
        
        # Get all employees
        employees = db.execute_query("SELECT * FROM employees ORDER BY city, theatre", fetch_all=True)
        
        if not employees:
            tk.Label(content_frame, text="No employees found", font=('Arial', 14), 
                    bg='#1a1a1a', fg='#888').pack(pady=50)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Table-style header
        table = tk.Frame(scrollable_frame, bg='#1a1a1a')
        table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        header_bg = '#333'
        cols = ["Name", "Designation", "City", "Theatre", "Salary", "Actions"]
        header = tk.Frame(table, bg=header_bg)
        header.grid(row=0, column=0, columnspan=6, sticky='ew')
        for i, col in enumerate(cols):
            tk.Label(header, text=col, font=('Arial', 11, 'bold'), bg=header_bg, fg='white', padx=10, pady=8).grid(row=0, column=i, sticky='w')
        for i in range(6):
            header.grid_columnconfigure(i, weight=1)

        # Rows
        for r, emp in enumerate(employees, start=1):
            row = tk.Frame(table, bg='#2a2a2a')
            row.grid(row=r, column=0, sticky='ew', pady=2)
            for i in range(6):
                row.grid_columnconfigure(i, weight=1)
            tk.Label(row, text=emp.get('name',''), font=('Arial', 10), bg='#2a2a2a', fg='white', padx=10, pady=6, anchor='w').grid(row=0, column=0, sticky='ew')
            tk.Label(row, text=emp.get('designation',''), font=('Arial', 10), bg='#2a2a2a', fg='white', padx=10, pady=6, anchor='w').grid(row=0, column=1, sticky='ew')
            tk.Label(row, text=emp.get('city',''), font=('Arial', 10), bg='#2a2a2a', fg='white', padx=10, pady=6, anchor='w').grid(row=0, column=2, sticky='ew')
            tk.Label(row, text=emp.get('theatre',''), font=('Arial', 10), bg='#2a2a2a', fg='white', padx=10, pady=6, anchor='w').grid(row=0, column=3, sticky='ew')
            tk.Label(row, text=f"₹{emp.get('salary',0)}", font=('Arial', 10, 'bold'), bg='#2a2a2a', fg='#4CAF50', padx=10, pady=6, anchor='w').grid(row=0, column=4, sticky='ew')
            actions = tk.Frame(row, bg='#2a2a2a')
            actions.grid(row=0, column=5, sticky='e', padx=8)
            tk.Button(actions, text="Edit", bg='#2196F3', fg='white', command=lambda e=emp: self.edit_employee_popup(e)).pack(side=tk.LEFT, padx=4)
            tk.Button(actions, text="Remove", bg='#d32f2f', fg='white', command=lambda eid=emp.get('employee_id'): self.delete_employee(eid)).pack(side=tk.LEFT, padx=4)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_screen_manager(self):
        """Show screen manager (delegated)"""
        if pages_admin:
            return pages_admin.show_screen_manager(self)
        # Fallback if import failed
        messagebox.showerror("Error", "Admin module not available")

    def show_manage_movies(self):
        """Show movie management (delegated)"""
        if pages_admin and hasattr(pages_admin, 'show_manage_movies'):
            return pages_admin.show_manage_movies(self)
        messagebox.showerror("Error", "Admin module not available")

    def reschedule_screen_popup(self, screen_id):
        rec = db.execute_query("SELECT * FROM scheduled_screens WHERE screen_id = ?", (screen_id,), fetch_one=True)
        if not rec:
            return
        popup = tk.Toplevel(self.root)
        popup.title("Reschedule")
        popup.geometry("400x260")
        popup.configure(bg='#1a1a1a')

        tk.Label(popup, text="New Date (YYYY-MM-DD)", bg='#1a1a1a', fg='white').pack(pady=5)
        date_var = tk.StringVar(value=rec['start_time'][:10])
        tk.Entry(popup, textvariable=date_var).pack()
        tk.Label(popup, text="Start Time (HH:MM)", bg='#1a1a1a', fg='white').pack(pady=5)
        st_var = tk.StringVar(value=datetime.fromisoformat(rec['start_time']).strftime('%H:%M'))
        tk.Entry(popup, textvariable=st_var).pack()
        tk.Label(popup, text="End Time (HH:MM)", bg='#1a1a1a', fg='white').pack(pady=5)
        et_var = tk.StringVar(value=datetime.fromisoformat(rec['end_time']).strftime('%H:%M'))
        tk.Entry(popup, textvariable=et_var).pack()

        def save():
            try:
                new_start = datetime.fromisoformat(f"{date_var.get()}T{st_var.get()}:00")
                new_end = datetime.fromisoformat(f"{date_var.get()}T{et_var.get()}:00")
            except Exception:
                messagebox.showerror("Error", "Invalid date/time format")
                return
            if new_end <= new_start:
                messagebox.showerror("Error", "End time must be after start time")
                return
            # Conflict detection
            if sched is not None:
                theatre_id = rec['theatre_id']
                screen_number = rec['screen_number']
                if sched.has_conflict(theatre_id, screen_number, new_start.isoformat(), new_end.isoformat(), exclude_screen_id=screen_id):
                    # suggest next slot roughly using current duration
                    duration_minutes = int((new_end - new_start).total_seconds() // 60)
                    suggestion = sched.suggest_next_slot(theatre_id, screen_number, new_start.isoformat(), duration_minutes, exclude_screen_id=screen_id)
                    if suggestion:
                        messagebox.showerror("Conflict", f"Overlaps with another show. Try next free slot: {suggestion[:16].replace('T',' ')}")
                    else:
                        messagebox.showerror("Conflict", "Overlaps with another show. Please choose a different time.")
                    return
                # City+movie per-day uniqueness (allow current screen via exclude)
                try:
                    city_row = db.execute_query("SELECT city FROM theatres WHERE theatre_id=?", (theatre_id,), fetch_one=True)
                    city_name = city_row['city'] if city_row else None
                    movie_id = rec['movie_id']
                    if city_name and movie_id and sched.has_city_movie_for_date(city_name, movie_id, new_start.isoformat(), exclude_screen_id=screen_id):
                        messagebox.showerror("Rule", "This movie already has a show scheduled in this city on the selected date")
                        return
                except Exception:
                    pass
            db.execute_query("UPDATE scheduled_screens SET start_time = ?, end_time = ? WHERE screen_id = ?", (new_start.isoformat(), new_end.isoformat(), screen_id))
            self.show_toast("Schedule updated")
            popup.destroy()
            self.refresh_page()

        tk.Button(popup, text="Save", bg='#4CAF50', fg='white', command=save).pack(pady=10)

    def unschedule_screen(self, screen_id):
        if not messagebox.askyesno("Confirm", "Unschedule this show and refund all bookings?"):
            return
        bookings = db.execute_query("SELECT * FROM bookings WHERE screen_id = ? AND status = 'confirmed'", (screen_id,), fetch_all=True)
        for b in bookings:
            user = db.execute_query("SELECT balance FROM users WHERE user_id = ?", (b['user_id'],), fetch_one=True)
            new_bal = (user['balance'] or 0) + (b['amount'] or 0)
            db.execute_query("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, b['user_id']))
            db.execute_query("UPDATE bookings SET status = 'cancelled', refunded_flag = 1 WHERE booking_id = ?", (b['booking_id'],))
        db.execute_query("DELETE FROM scheduled_screens WHERE screen_id = ?", (screen_id,))
        self.show_toast("Show unscheduled and refunded")
        self.refresh_page()

    def admin_schedule_screen_popup(self, city_default=None, date_default=None, on_success=None):
        popup = tk.Toplevel(self.root)
        popup.title("Schedule New Show")
        popup.geometry("520x520")
        popup.configure(bg='#1a1a1a')

        # Inputs
        tk.Label(popup, text="City", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        cities_rows = db.execute_query("SELECT DISTINCT city FROM theatres", fetch_all=True) or []
        cities = sorted([r['city'] for r in cities_rows])
        city_var = tk.StringVar(value=city_default if city_default in cities else (cities[0] if cities else ''))
        ttk.Combobox(popup, textvariable=city_var, values=cities, state='readonly', width=24).pack()

        tk.Label(popup, text="Theatre", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        def theatres_for_city():
            return db.execute_query("SELECT theatre_id, name FROM theatres WHERE city = ?", (city_var.get(),), fetch_all=True) or []
        theatre_rows = theatres_for_city()
        theatre_map = {f"{r['name']} (#{r['theatre_id']})": r['theatre_id'] for r in theatre_rows}
        theatre_names = list(theatre_map.keys())
        theatre_var = tk.StringVar(value=(theatre_names[0] if theatre_names else ''))
        theatre_combo = ttk.Combobox(popup, textvariable=theatre_var, values=theatre_names, state='readonly', width=36)
        theatre_combo.pack()

        def refresh_theatres(*_):
            rows = theatres_for_city()
            nonlocal theatre_map
            theatre_map = {f"{r['name']} (#{r['theatre_id']})": r['theatre_id'] for r in rows}
            names = list(theatre_map.keys())
            theatre_combo['values'] = names
            if names:
                theatre_var.set(names[0])
            else:
                theatre_var.set('')
        city_var.trace_add('write', refresh_theatres)

        tk.Label(popup, text="Movie", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        movies = db.execute_query("SELECT movie_id, title FROM movies ORDER BY title", fetch_all=True) or []
        movie_map = {f"{m['title']} (#{m['movie_id']})": m['movie_id'] for m in movies}
        movie_names = list(movie_map.keys())
        movie_var = tk.StringVar(value=(movie_names[0] if movie_names else ''))
        ttk.Combobox(popup, textvariable=movie_var, values=movie_names, state='readonly', width=36).pack()

        tk.Label(popup, text="Screen Number", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        screen_var = tk.StringVar(value='1')
        tk.Entry(popup, textvariable=screen_var).pack()

        tk.Label(popup, text="Date (YYYY-MM-DD)", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        date_var = tk.StringVar(value=(date_default if date_default else datetime.now().strftime('%Y-%m-%d')))
        tk.Entry(popup, textvariable=date_var).pack()

        tk.Label(popup, text="Start (HH:MM)", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        st_var = tk.StringVar(value='10:00')
        tk.Entry(popup, textvariable=st_var).pack()
        tk.Label(popup, text="End (HH:MM)", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        et_var = tk.StringVar(value='13:00')
        tk.Entry(popup, textvariable=et_var).pack()

        tk.Label(popup, text="Prices (E/C/P)", bg='#1a1a1a', fg='white').pack(pady=(10,2))
        pe_var = tk.StringVar(value='150')
        pc_var = tk.StringVar(value='220')
        pp_var = tk.StringVar(value='320')
        f_prices = tk.Frame(popup, bg='#1a1a1a'); f_prices.pack()
        tk.Entry(f_prices, textvariable=pe_var, width=8).pack(side=tk.LEFT, padx=4)
        tk.Entry(f_prices, textvariable=pc_var, width=8).pack(side=tk.LEFT, padx=4)
        tk.Entry(f_prices, textvariable=pp_var, width=8).pack(side=tk.LEFT, padx=4)

        def save_new():
            if not theatre_var.get() or not movie_var.get():
                messagebox.showerror("Error", "Select theatre and movie")
                return
            try:
                theatre_id = theatre_map[theatre_var.get()]
                movie_id = movie_map[movie_var.get()]
                screen_number = int(screen_var.get())
                start_dt = datetime.fromisoformat(f"{date_var.get()}T{st_var.get()}:00")
                end_dt = datetime.fromisoformat(f"{date_var.get()}T{et_var.get()}:00")
                pe = float(pe_var.get()); pc = float(pc_var.get()); pp = float(pp_var.get())
            except Exception:
                messagebox.showerror("Error", "Invalid input values")
                return
            if end_dt <= start_dt:
                messagebox.showerror("Error", "End time must be after start time")
                return
            # 1) Same theatre+screen conflict check
            if sched is not None and sched.has_conflict(theatre_id, screen_number, start_dt.isoformat(), end_dt.isoformat()):
                messagebox.showerror("Conflict", "Overlaps with another show on the same screen")
                return
            # 2) City+movie per-day uniqueness
            if sched is not None and sched.has_city_movie_for_date(city_var.get(), movie_id, start_dt.isoformat()):
                messagebox.showerror("Rule", "This movie already has a show scheduled in this city on the selected date")
                return
            # Insert with default 10x10 seat map of zeros
            seat_map = [[0 for _ in range(10)] for _ in range(10)]
            db.execute_query(
                """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number, start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (theatre_id, movie_id, screen_number, start_dt.isoformat(), end_dt.isoformat(), json.dumps(seat_map), pe, pc, pp)
            )
            self.show_toast("Show scheduled")
            popup.destroy()
            if callable(on_success):
                on_success()

        tk.Button(popup, text="Save", bg='#4CAF50', fg='white', command=save_new).pack(pady=12)
    
    def show_admin_feedback(self):
        """Show admin feedback page (delegated)"""
        if pages_admin:
            return pages_admin.show_admin_feedback(self)
        messagebox.showerror("Error", "Admin module not available")
    
    def mark_feedback_read(self, feedback_id):
        """Mark feedback as read"""
        db.execute_query(
            "UPDATE feedbacks SET read_flag = 1 WHERE feedback_id = ?",
            (feedback_id,)
        )
        self.show_toast("Feedback marked as read")
        self.refresh_page()

    def reset_all_passwords(self):
        """Set every account's password to 'password123' and refresh credentials file"""
        db.execute_query("UPDATE users SET password = 'password123'")
        try:
            self.export_credentials_to_file()
        except Exception:
            pass
        self.show_toast("All user passwords reset to 'password123'")
        self.refresh_page()


if __name__ == "__main__":
    root = tk.Tk()
    app = theatre_booking_app(root)
    root.mainloop()
