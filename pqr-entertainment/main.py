"""
Theatre Booking Management System - Complete Application
PQR Entertainment PaaS Desktop Application

Entry point: main.py
Packaging: pyinstaller --onefile --noconsole main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import database as db
from datetime import datetime
import json
import os

# Global state
current_user = None
current_role = None
admin_stack = []
producer_stack = []
user_stack = []
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
        
        # Start with login page
        self.show_login_page()
    
    def clear_container(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
        global menu_visible
        menu_visible = False
    
    def add_navigation_bar(self):
        """Add navigation bar with forward/backward/refresh buttons"""
        nav_frame = tk.Frame(self.main_container, bg='#2a2a2a', height=40)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        
        btn_style = {'bg': '#444', 'fg': 'white', 'font': ('Arial', 10), 
                     'borderwidth': 0, 'padx': 10, 'pady': 5}
        
        tk.Button(nav_frame, text="← Back", command=self.go_back, **btn_style).pack(side=tk.LEFT, padx=5)
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
            tk.Button(self.menu_overlay, text="👤 My Profile", 
                     command=lambda: self.navigate_to('user_profile'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎫 My Bookings", 
                     command=lambda: self.navigate_to('my_bookings'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📜 Booking History", 
                     command=lambda: self.navigate_to('booking_history'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="⭐ Watchlist", 
                     command=lambda: self.navigate_to('watchlist'), **menu_style).pack(fill=tk.X)
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
            tk.Button(self.menu_overlay, text="💬 Feedback", 
                     command=lambda: self.navigate_to('admin_feedback'), **menu_style).pack(fill=tk.X)
        
        tk.Button(self.menu_overlay, text="🚪 Logout", 
                 command=self.logout, bg='#d32f2f', fg='white', 
                 font=('Arial', 12), pady=10).pack(side=tk.BOTTOM, fill=tk.X)
    
    def navigate_to(self, page_name):
        """Navigate to a specific page"""
        if self.menu_overlay:
            self.toggle_menu()
        
        # Add to navigation stack
        global current_role, admin_stack, producer_stack, user_stack
        if current_role == 'admin':
            admin_stack.append(page_name)
        elif current_role == 'producer':
            producer_stack.append(page_name)
        elif current_role == 'user':
            user_stack.append(page_name)
        
        # Route to appropriate page
        routes = {
            'user_home': self.show_user_home,
            'user_profile': self.show_user_profile,
            'my_bookings': self.show_my_bookings,
            'booking_history': self.show_booking_history,
            'watchlist': self.show_watchlist,
            'wallet': self.show_wallet,
            'feedback': self.show_feedback_form,
            'producer_dashboard': self.show_producer_dashboard,
            'add_content': self.show_add_content,
            'admin_profile': self.show_admin_profile,
            'cinema_halls': self.show_cinema_halls,
            'employees': self.show_employees,
            'screen_manager': self.show_screen_manager,
            'admin_feedback': self.show_admin_feedback,
        }
        
        if page_name in routes:
            routes[page_name]()
    
    def go_back(self):
        """Navigate backward"""
        global current_role, admin_stack, producer_stack, user_stack
        stack = admin_stack if current_role == 'admin' else producer_stack if current_role == 'producer' else user_stack
        
        if len(stack) > 1:
            stack.pop()  # Remove current
            page = stack.pop()  # Get previous
            self.navigate_to(page)
    
    def refresh_page(self):
        """Refresh current page"""
        global current_role, admin_stack, producer_stack, user_stack
        stack = admin_stack if current_role == 'admin' else producer_stack if current_role == 'producer' else user_stack
        
        if stack:
            page = stack[-1]
            stack.pop()
            self.navigate_to(page)
    
    def perform_search(self):
        """Perform search"""
        query = self.search_var.get()
        if not query:
            return
        
        # Search movies
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
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
    
    def logout(self):
        """Logout user"""
        global current_user, current_role, admin_stack, producer_stack, user_stack
        
        if current_role == 'admin':
            admin_stack.clear()
        elif current_role == 'producer':
            producer_stack.clear()
        elif current_role == 'user':
            user_stack.clear()
        
        current_user = None
        current_role = None
        
        self.show_login_page()
    
    # ==================== AUTHENTICATION PAGES ====================
    
    def show_login_page(self):
        """Show login page"""
        self.clear_container()
        
        # Center frame
        center_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        tk.Label(center_frame, text="PQR Entertainment", font=('Arial', 28, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        tk.Label(center_frame, text="Theatre Booking Management System", 
                font=('Arial', 14), bg='#1a1a1a', fg='#888').pack(pady=5)
        
        # Login form
        form_frame = tk.Frame(center_frame, bg='#2a2a2a', padx=40, pady=40)
        form_frame.pack(pady=30)
        
        tk.Label(form_frame, text="Username", font=('Arial', 12), 
                bg='#2a2a2a', fg='white').grid(row=0, column=0, sticky='w', pady=5)
        username_entry = tk.Entry(form_frame, font=('Arial', 12), width=30)
        username_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Password", font=('Arial', 12), 
                bg='#2a2a2a', fg='white').grid(row=1, column=0, sticky='w', pady=5)
        password_entry = tk.Entry(form_frame, font=('Arial', 12), width=30, show='*')
        password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        def attempt_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            user = db.execute_query(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password), fetch_one=True
            )
            
            if user:
                global current_user, current_role
                current_user = user
                current_role = user['role']
                
                if current_role == 'user':
                    self.show_user_home()
                elif current_role == 'producer':
                    self.show_producer_dashboard()
                elif current_role == 'admin':
                    self.show_admin_profile()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        
        tk.Button(form_frame, text="Login", font=('Arial', 12, 'bold'), 
                 bg='#4CAF50', fg='white', width=15, command=attempt_login).grid(
                 row=2, column=0, columnspan=2, pady=20)
        
        # Registration buttons
        reg_frame = tk.Frame(center_frame, bg='#1a1a1a')
        reg_frame.pack(pady=10)
        
        tk.Label(reg_frame, text="New here?", font=('Arial', 11), 
                bg='#1a1a1a', fg='white').pack()
        
        btn_frame = tk.Frame(reg_frame, bg='#1a1a1a')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Register as User", font=('Arial', 10), 
                 bg='#2196F3', fg='white', command=lambda: self.show_register_page('user')).pack(
                 side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Register as Producer/Host", font=('Arial', 10), 
                 bg='#FF9800', fg='white', command=lambda: self.show_register_page('producer')).pack(
                 side=tk.LEFT, padx=5)
    
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
            self.show_login_page()
        
        tk.Button(form_frame, text="Register", font=('Arial', 12, 'bold'), 
                 bg='#4CAF50', fg='white', width=15, 
                 command=attempt_register).grid(row=6 if role == 'producer' else 5, 
                                               column=0, columnspan=2, pady=20)
        
        tk.Button(center_frame, text="← Back to Login", font=('Arial', 10), 
                 bg='#555', fg='white', command=self.show_login_page).pack(pady=10)
    
    # ==================== USER PAGES ====================
    
    def show_user_home(self):
        """Show user homepage with movies"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_search=True, show_username=True)
        
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
        
        # Welcome banner
        banner_frame = tk.Frame(scrollable_frame, bg='#2a2a2a')
        banner_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(banner_frame, text="🎬 Browse Movies & Events", 
                font=('Arial', 24, 'bold'), bg='#2a2a2a', fg='white').pack(pady=20)
        
        # Get all movies
        movies = db.execute_query("SELECT * FROM movies ORDER BY average_rating DESC", fetch_all=True)
        
        # Movie grid
        self.create_movie_grid(scrollable_frame, movies)
        
        # Footer
        footer_frame = tk.Frame(scrollable_frame, bg='#2a2a2a')
        footer_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(footer_frame, text="Contact Us: contact@pqrentertainment.com", 
                font=('Arial', 10), bg='#2a2a2a', fg='#888').pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
    
    def create_movie_grid(self, parent, movies):
        """Create grid of movie cards"""
        grid_frame = tk.Frame(parent, bg='#1a1a1a')
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for idx, movie in enumerate(movies):
            row = idx // 4
            col = idx % 4
            
            # Movie card
            card = tk.Frame(grid_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Image placeholder
            img_frame = tk.Frame(card, bg='#444', width=180, height=240)
            img_frame.pack(pady=10)
            img_frame.pack_propagate(False)
            tk.Label(img_frame, text="🎬", font=('Arial', 40), bg='#444', fg='white').pack(expand=True)
            
            # Movie info
            tk.Label(card, text=movie['title'], font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white', wraplength=180).pack(pady=5)
            
            # Rating
            rating_text = f"⭐ {movie['average_rating']}/5.0"
            tk.Label(card, text=rating_text, font=('Arial', 10), 
                    bg='#2a2a2a', fg='#FFD700').pack()
            
            # Languages
            try:
                languages = json.loads(movie['languages_json'])
                lang_text = ', '.join(languages[:2])
                tk.Label(card, text=lang_text, font=('Arial', 9), 
                        bg='#2a2a2a', fg='#888').pack()
            except:
                pass
            
            # Book button
            tk.Button(card, text="Book Tickets", bg='#4CAF50', fg='white', 
                     font=('Arial', 10, 'bold'), command=lambda m=movie: self.show_movie_detail(m)).pack(pady=10)
        
        # Configure grid columns
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
    
    def show_movie_detail(self, movie):
        """Show movie details and booking options"""
        self.current_movie_id = movie['movie_id']
        
        # Create popup
        popup = tk.Toplevel(self.root)
        popup.title(movie['title'])
        popup.geometry("600x700")
        popup.configure(bg='#1a1a1a')
        
        # Scrollable frame
        canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        detail_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        detail_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=detail_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Movie details
        tk.Label(detail_frame, text=movie['title'], font=('Arial', 24, 'bold'), 
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Rating
        tk.Label(detail_frame, text=f"⭐ {movie['average_rating']}/5.0", 
                font=('Arial', 14), bg='#1a1a1a', fg='#FFD700').pack()
        
        # Description
        if movie['description']:
            desc_frame = tk.Frame(detail_frame, bg='#2a2a2a')
            desc_frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(desc_frame, text=movie['description'], font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc', wraplength=500, justify='left').pack(anchor='w', padx=10, pady=5)
        
        # Actors
        try:
            actors = json.loads(movie['actors_json'])
            actors_frame = tk.Frame(detail_frame, bg='#2a2a2a')
            actors_frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(actors_frame, text="Cast:", font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(actors_frame, text=', '.join(actors), font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc', wraplength=500).pack(anchor='w', padx=10, pady=5)
        except:
            pass
        
        # Languages
        try:
            languages = json.loads(movie['languages_json'])
            lang_frame = tk.Frame(detail_frame, bg='#2a2a2a')
            lang_frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(lang_frame, text="Languages:", font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(lang_frame, text=', '.join(languages), font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
        except:
            pass
        
        # Genres
        try:
            genres = json.loads(movie['genres_json'])
            genre_frame = tk.Frame(detail_frame, bg='#2a2a2a')
            genre_frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(genre_frame, text="Genres:", font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            tk.Label(genre_frame, text=', '.join(genres), font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
        except:
            pass
        
        # Duration
        duration_mins = movie['duration_seconds'] // 60
        hours = duration_mins // 60
        mins = duration_mins % 60
        duration_frame = tk.Frame(detail_frame, bg='#2a2a2a')
        duration_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(duration_frame, text=f"Duration: {hours}h {mins}m", font=('Arial', 11), 
                bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=10, pady=5)
        
        # Watchlist button
        watchlist_check = db.execute_query(
            "SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (current_user['user_id'], movie['movie_id']), fetch_one=True
        )
        
        if watchlist_check:
            tk.Button(detail_frame, text="❤ Remove from Watchlist", bg='#f44336', fg='white',
                     font=('Arial', 12), command=lambda: self.remove_from_watchlist(movie['movie_id'], popup)).pack(pady=10)
        else:
            tk.Button(detail_frame, text="❤ Add to Watchlist", bg='#FF9800', fg='white',
                     font=('Arial', 12), command=lambda: self.add_to_watchlist(movie['movie_id'], popup)).pack(pady=10)
        
        # Book button
        tk.Button(detail_frame, text="🎫 Book Tickets", bg='#4CAF50', fg='white',
                 font=('Arial', 14, 'bold'), command=lambda: [popup.destroy(), self.show_city_selection()]).pack(pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
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
    
    def show_city_selection(self):
        """Show city selection popup for booking"""
        popup = tk.Toplevel(self.root)
        popup.title("Select City")
        popup.geometry("400x300")
        popup.configure(bg='#1a1a1a')
        
        tk.Label(popup, text="Select City", font=('Arial', 20, 'bold'), 
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        cities = ['Mumbai', 'Pune', 'Nashik', 'Bangalore']
        
        for city in cities:
            tk.Button(popup, text=city, font=('Arial', 14), bg='#2196F3', fg='white',
                     width=20, command=lambda c=city: [popup.destroy(), self.show_theatre_listing(c)]).pack(pady=10)
    
    def show_theatre_listing(self, city):
        """Show theatres and showtimes for selected city"""
        # Get screens for this movie in this city
        query = """
            SELECT ss.*, t.name as theatre_name, t.seating_schema_json, m.title as movie_title
            FROM scheduled_screens ss
            JOIN theatres t ON ss.theatre_id = t.theatre_id
            JOIN movies m ON ss.movie_id = m.movie_id
            WHERE t.city = ? AND ss.movie_id = ?
            AND DATE(ss.start_time) >= DATE('now')
            AND DATE(ss.start_time) <= DATE('now', '+3 days')
            ORDER BY ss.start_time
        """
        
        screens = db.execute_query(query, (city, self.current_movie_id), fetch_all=True)
        
        if not screens:
            messagebox.showinfo("No Shows", f"No shows available in {city} for this movie.")
            return
        
        # Create popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Theatres in {city}")
        popup.geometry("700x600")
        popup.configure(bg='#1a1a1a')
        
        # Header
        tk.Label(popup, text=f"Theatres in {city}", font=('Arial', 20, 'bold'), 
                bg='#1a1a1a', fg='white').pack(pady=10)
        tk.Label(popup, text=screens[0]['movie_title'], font=('Arial', 14), 
                bg='#1a1a1a', fg='#888').pack()
        
        # Scrollable frame
        canvas = tk.Canvas(popup, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        theatre_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        theatre_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=theatre_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Group by theatre
        theatres = {}
        for screen in screens:
            if screen['theatre_name'] not in theatres:
                theatres[screen['theatre_name']] = []
            theatres[screen['theatre_name']].append(screen)
        
        # Display each theatre
        for theatre_name, shows in theatres.items():
            theatre_card = tk.Frame(theatre_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            theatre_card.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Label(theatre_card, text=theatre_name, font=('Arial', 14, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=5)
            
            # Show times
            for show in shows:
                show_time = datetime.fromisoformat(show['start_time'])
                time_str = show_time.strftime("%d %b, %I:%M %p")
                
                # Calculate available seats
                try:
                    seat_map = json.loads(show['seat_map_json'])
                    booked = sum(row.count(1) for row in seat_map)
                    available = 100 - booked
                except:
                    available = 100
                
                show_frame = tk.Frame(theatre_card, bg='#333')
                show_frame.pack(fill=tk.X, padx=10, pady=5)
                
                tk.Label(show_frame, text=f"{time_str} | Screen {show['screen_number']}", 
                        font=('Arial', 11), bg='#333', fg='white').pack(side=tk.LEFT, padx=10)
                tk.Label(show_frame, text=f"{available} seats", 
                        font=('Arial', 10), bg='#333', fg='#4CAF50').pack(side=tk.LEFT, padx=10)
                
                tk.Button(show_frame, text="Select", bg='#4CAF50', fg='white',
                         command=lambda s=show: [popup.destroy(), self.show_seat_selection(s)]).pack(side=tk.RIGHT, padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_seat_selection(self, screen_data):
        """Show seat selection matrix"""
        self.current_screen_id = screen_data['screen_id']
        self.selected_seats = []
        
        # Create popup
        popup = tk.Toplevel(self.root)
        popup.title("Select Seats")
        popup.geometry("900x700")
        popup.configure(bg='#1a1a1a')
        
        # Header
        header_frame = tk.Frame(popup, bg='#2a2a2a')
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="Select Your Seats", font=('Arial', 18, 'bold'), 
                bg='#2a2a2a', fg='white').pack(pady=10)
        
        show_time = datetime.fromisoformat(screen_data['start_time'])
        time_str = show_time.strftime("%d %b %Y, %I:%M %p")
        tk.Label(header_frame, text=f"{screen_data['theatre_name']} - Screen {screen_data['screen_number']}", 
                font=('Arial', 12), bg='#2a2a2a', fg='#888').pack()
        tk.Label(header_frame, text=time_str, font=('Arial', 11), 
                bg='#2a2a2a', fg='#888').pack(pady=5)
        
        # Screen label
        screen_label_frame = tk.Frame(popup, bg='#1a1a1a')
        screen_label_frame.pack(pady=20)
        tk.Label(screen_label_frame, text="═══════════ SCREEN ═══════════", 
                font=('Arial', 14, 'bold'), bg='#1a1a1a', fg='white').pack()
        
        # Seat matrix frame
        seat_frame = tk.Frame(popup, bg='#1a1a1a')
        seat_frame.pack(pady=20)
        
        # Load seat map
        try:
            seat_map = json.loads(screen_data['seat_map_json'])
        except:
            seat_map = [[0 for _ in range(10)] for _ in range(10)]
        
        # Prices
        price_economy = screen_data['price_economy']
        price_central = screen_data['price_central']
        price_premium = screen_data['price_premium']
        
        # Create seat buttons
        seat_buttons = {}
        rows = ['J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        
        for row_idx, row_label in enumerate(rows):
            # Row label
            tk.Label(seat_frame, text=row_label, font=('Arial', 12, 'bold'), 
                    bg='#1a1a1a', fg='white').grid(row=row_idx, column=0, padx=5)
            
            for col in range(10):
                seat_num = f"{row_label}{col + 1}"
                is_booked = seat_map[row_idx][col] == 1
                
                # Determine price based on row (cinema layout)
                if row_idx < 3:  # J, I, H - Recliner
                    price = price_premium
                    section = "Recliner"
                elif row_idx < 7:  # G, F, E, D - Central
                    price = price_central
                    section = "Central"
                else:  # C, B, A - Economy
                    price = price_economy
                    section = "Economy"
                
                btn = tk.Button(seat_frame, text=seat_num, width=6, height=2,
                               bg='#666' if is_booked else '#fff',
                               fg='white' if is_booked else 'black',
                               state=tk.DISABLED if is_booked else tk.NORMAL)
                
                btn.grid(row=row_idx, column=col + 1, padx=2, pady=2)
                
                if not is_booked:
                    btn.config(command=lambda b=btn, s=seat_num, p=price: self.toggle_seat(b, s, p))
                
                seat_buttons[seat_num] = (btn, price)
        
        # Legend
        legend_frame = tk.Frame(popup, bg='#1a1a1a')
        legend_frame.pack(pady=10)
        
        tk.Label(legend_frame, text="■ Available", bg='#1a1a1a', fg='white', 
                font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="■ Selected", bg='#4CAF50', fg='white', 
                font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="■ Booked", bg='#666', fg='white', 
                font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        # Price info
        price_frame = tk.Frame(popup, bg='#2a2a2a')
        price_frame.pack(fill=tk.X, pady=10)
        tk.Label(price_frame, text=f"Economy (A-C): ₹{price_economy}  |  Central (D-G): ₹{price_central}  |  Recliner (H-J): ₹{price_premium}", 
                font=('Arial', 11), bg='#2a2a2a', fg='white').pack(pady=5)
        
        # Total and proceed
        bottom_frame = tk.Frame(popup, bg='#1a1a1a')
        bottom_frame.pack(fill=tk.X, pady=20)
        
        self.total_label = tk.Label(bottom_frame, text="Total: ₹0", font=('Arial', 16, 'bold'), 
                                    bg='#1a1a1a', fg='white')
        self.total_label.pack(side=tk.LEFT, padx=20)
        
        tk.Button(bottom_frame, text="Proceed to Payment", bg='#4CAF50', fg='white',
                 font=('Arial', 14, 'bold'), command=lambda: [popup.destroy(), self.process_payment(screen_data)]).pack(side=tk.RIGHT, padx=20)
    
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
                (current_user['user_id'], self.current_screen_id, seat, amount, 
                 datetime.now().isoformat())
            )
        
        # Update seat map
        db.execute_query(
            "UPDATE scheduled_screens SET seat_map_json = ? WHERE screen_id = ?",
            (json.dumps(seat_map), self.current_screen_id)
        )
        
        messagebox.showinfo("Success", 
                          f"Booking confirmed!\n\n{len(self.selected_seats)} seat(s) booked\nTotal: ₹{total}\nRemaining balance: ₹{new_balance}")
        
        self.navigate_to('my_bookings')
    
    def show_wallet(self):
        """Show wallet page"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        # Refresh user data
        user = db.execute_query(
            "SELECT balance FROM users WHERE user_id = ?",
            (current_user['user_id'],), fetch_one=True
        )
        current_user['balance'] = user['balance']
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="💰 My Wallet", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Balance display
        balance_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
        balance_frame.pack(pady=20)
        
        tk.Label(balance_frame, text="Current Balance", font=('Arial', 14), 
                bg='#2a2a2a', fg='#888').pack(pady=10, padx=50)
        tk.Label(balance_frame, text=f"₹{current_user['balance']:.2f}", 
                font=('Arial', 32, 'bold'), bg='#2a2a2a', fg='#4CAF50').pack(pady=10, padx=50)
        
        # Add balance section
        add_frame = tk.Frame(content_frame, bg='#1a1a1a')
        add_frame.pack(pady=20)
        
        tk.Label(add_frame, text="Add Balance:", font=('Arial', 14), 
                bg='#1a1a1a', fg='white').pack()
        
        # Quick add buttons
        quick_frame = tk.Frame(add_frame, bg='#1a1a1a')
        quick_frame.pack(pady=10)
        
        amounts = [500, 1000, 2000, 5000]
        for amount in amounts:
            tk.Button(quick_frame, text=f"+ ₹{amount}", bg='#2196F3', fg='white',
                     font=('Arial', 12), width=10, 
                     command=lambda a=amount: self.add_balance(a)).pack(side=tk.LEFT, padx=5)
        
        # Custom amount
        custom_frame = tk.Frame(add_frame, bg='#1a1a1a')
        custom_frame.pack(pady=10)
        
        tk.Label(custom_frame, text="Custom Amount:", font=('Arial', 11), 
                bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=5)
        
        amount_var = tk.StringVar()
        tk.Entry(custom_frame, textvariable=amount_var, font=('Arial', 12), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(custom_frame, text="Add", bg='#4CAF50', fg='white',
                 font=('Arial', 11), command=lambda: self.add_balance(float(amount_var.get() or 0))).pack(side=tk.LEFT, padx=5)
        
        # Recent transactions
        tk.Label(content_frame, text="Recent Transactions", font=('Arial', 16, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        bookings = db.execute_query(
            """SELECT b.*, m.title, ss.start_time 
               FROM bookings b
               JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
               JOIN movies m ON ss.movie_id = m.movie_id
               WHERE b.user_id = ?
               ORDER BY b.booking_date DESC LIMIT 10""",
            (current_user['user_id'],), fetch_all=True
        )
        
        if bookings:
            trans_frame = tk.Frame(content_frame, bg='#2a2a2a')
            trans_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            for booking in bookings:
                tk.Label(trans_frame, text=f"- ₹{booking['amount']:.2f} | {booking['title']} | {booking['seat']}", 
                        font=('Arial', 11), bg='#2a2a2a', fg='#ccc', anchor='w').pack(fill=tk.X, padx=10, pady=2)
    
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
        """Show watchlist"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="⭐ My Watchlist", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Get watchlist items
        watchlist = db.execute_query(
            """SELECT w.*, m.title, m.average_rating, m.languages_json, m.genres_json
               FROM watchlist w
               JOIN movies m ON w.movie_id = m.movie_id
               WHERE w.user_id = ?""",
            (current_user['user_id'],), fetch_all=True
        )
        
        if not watchlist:
            tk.Label(content_frame, text="Your watchlist is empty", font=('Arial', 14), 
                    bg='#1a1a1a', fg='#888').pack(pady=50)
            tk.Label(content_frame, text="Add movies from the homepage!", font=('Arial', 12), 
                    bg='#1a1a1a', fg='#888').pack()
            return
        
        # Display watchlist
        for item in watchlist:
            item_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            item_frame.pack(fill=tk.X, pady=10)
            
            # Info
            info_frame = tk.Frame(item_frame, bg='#2a2a2a')
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            tk.Label(info_frame, text=item['title'], font=('Arial', 14, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w')
            tk.Label(info_frame, text=f"⭐ {item['average_rating']}/5.0", font=('Arial', 11), 
                    bg='#2a2a2a', fg='#FFD700').pack(anchor='w')
            
            try:
                languages = json.loads(item['languages_json'])
                tk.Label(info_frame, text=', '.join(languages), font=('Arial', 10), 
                        bg='#2a2a2a', fg='#888').pack(anchor='w')
            except:
                pass
            
            # Buttons
            btn_frame = tk.Frame(item_frame, bg='#2a2a2a')
            btn_frame.pack(side=tk.RIGHT, padx=20)
            
            # Get full movie data
            movie = db.execute_query(
                "SELECT * FROM movies WHERE movie_id = ?",
                (item['movie_id'],), fetch_one=True
            )
            
            tk.Button(btn_frame, text="Visit", bg='#4CAF50', fg='white',
                     font=('Arial', 11), width=10,
                     command=lambda m=movie: self.show_movie_detail(m)).pack(pady=5)
            tk.Button(btn_frame, text="Remove", bg='#f44336', fg='white',
                     font=('Arial', 11), width=10,
                     command=lambda mid=item['movie_id']: self.remove_from_watchlist_page(mid)).pack(pady=5)
    
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
        """Show upcoming bookings"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="🎫 My Bookings", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Get upcoming bookings
        bookings = db.execute_query(
            """SELECT b.*, m.title, ss.start_time, t.name as theatre_name, t.city, ss.screen_number
               FROM bookings b
               JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
               JOIN movies m ON ss.movie_id = m.movie_id
               JOIN theatres t ON ss.theatre_id = t.theatre_id
               WHERE b.user_id = ? AND DATE(ss.start_time) >= DATE('now')
               ORDER BY ss.start_time""",
            (current_user['user_id'],), fetch_all=True
        )
        
        if not bookings:
            tk.Label(content_frame, text="No upcoming bookings", font=('Arial', 14), 
                    bg='#1a1a1a', fg='#888').pack(pady=50)
            return
        
        # Display bookings
        for booking in bookings:
            booking_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            booking_frame.pack(fill=tk.X, pady=10)
            
            # Info
            tk.Label(booking_frame, text=booking['title'], font=('Arial', 14, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=20, pady=5)
            
            show_time = datetime.fromisoformat(booking['start_time'])
            time_str = show_time.strftime("%d %b %Y, %I:%M %p")
            
            tk.Label(booking_frame, text=f"📅 {time_str}", font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
            tk.Label(booking_frame, text=f"🏢 {booking['theatre_name']}, {booking['city']}", font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
            tk.Label(booking_frame, text=f"💺 Seat: {booking['seat']} | Screen: {booking['screen_number']}", 
                    font=('Arial', 11), bg='#2a2a2a', fg='#ccc').pack(anchor='w', padx=20)
            tk.Label(booking_frame, text=f"💰 ₹{booking['amount']}", font=('Arial', 12, 'bold'), 
                    bg='#2a2a2a', fg='#4CAF50').pack(anchor='w', padx=20, pady=5)
    
    def show_booking_history(self):
        """Show all booking history"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="📜 Booking History", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Get all bookings
        bookings = db.execute_query(
            """SELECT b.*, m.title, ss.start_time, t.name as theatre_name, t.city, ss.screen_number
               FROM bookings b
               JOIN scheduled_screens ss ON b.screen_id = ss.screen_id
               JOIN movies m ON ss.movie_id = m.movie_id
               JOIN theatres t ON ss.theatre_id = t.theatre_id
               WHERE b.user_id = ?
               ORDER BY ss.start_time DESC""",
            (current_user['user_id'],), fetch_all=True
        )
        
        if not bookings:
            tk.Label(content_frame, text="No bookings yet", font=('Arial', 14), 
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
        
        # Display bookings
        for booking in bookings:
            booking_frame = tk.Frame(scrollable_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=1)
            booking_frame.pack(fill=tk.X, pady=5, padx=10)
            
            show_time = datetime.fromisoformat(booking['start_time'])
            time_str = show_time.strftime("%d %b %Y, %I:%M %p")
            
            tk.Label(booking_frame, text=f"{booking['title']} | {time_str} | {booking['theatre_name']}, {booking['city']} | Seat: {booking['seat']} | ₹{booking['amount']}", 
                    font=('Arial', 10), bg='#2a2a2a', fg='#ccc', anchor='w').pack(fill=tk.X, padx=10, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
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
        """Show producer dashboard - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_search=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Producer Dashboard", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        tk.Label(content_frame, text="Content management features coming soon", 
                font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    
    def show_add_content(self):
        """Show add content page - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Add Movie/Event", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        tk.Label(content_frame, text="Upload features coming soon", 
                font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    
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
    
    def show_cinema_halls(self):
        """Show cinema halls management"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="🎬 Cinema Halls Management", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
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
        
        # Display by city
        for city, city_theatres in cities.items():
            city_frame = tk.Frame(scrollable_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            city_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(city_frame, text=city, font=('Arial', 16, 'bold'), 
                    bg='#2a2a2a', fg='white').pack(anchor='w', padx=10, pady=10)
            
            for theatre in city_theatres:
                theatre_row = tk.Frame(city_frame, bg='#333')
                theatre_row.pack(fill=tk.X, padx=10, pady=2)
                
                try:
                    schema = json.loads(theatre['seating_schema_json'])
                    badges = []
                    if schema.get('3d'):
                        badges.append("3D")
                    if schema.get('imax'):
                        badges.append("IMAX")
                    badge_text = " | ".join(badges) if badges else ""
                except:
                    badge_text = ""
                
                tk.Label(theatre_row, text=f"{theatre['name']} {badge_text}", 
                        font=('Arial', 12), bg='#333', fg='white', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_employees(self):
        """Show employees management"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="👥 Employee Management", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
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
        
        # Display employees
        for emp in employees:
            emp_frame = tk.Frame(scrollable_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=1)
            emp_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(emp_frame, text=f"{emp['name']} | {emp['designation']} | {emp['city']} - {emp['theatre']} | ₹{emp['salary']}", 
                    font=('Arial', 11), bg='#2a2a2a', fg='white', anchor='w').pack(fill=tk.X, padx=10, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_screen_manager(self):
        """Show screen manager - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="📺 Screen Manager", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        tk.Label(content_frame, text="Schedule management features coming soon", 
                font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    
    def show_admin_feedback(self):
        """Show admin feedback page"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="💬 User Feedback", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        # Get unread feedback
        feedbacks = db.execute_query(
            """SELECT f.*, u.name as user_name
               FROM feedbacks f
               JOIN users u ON f.user_id = u.user_id
               WHERE f.read_flag = 0
               ORDER BY f.timestamp DESC LIMIT 10""",
            fetch_all=True
        )
        
        if not feedbacks:
            tk.Label(content_frame, text="No unread feedback", font=('Arial', 14), 
                    bg='#1a1a1a', fg='#888').pack(pady=50)
            return
        
        # Display feedback
        for feedback in feedbacks:
            feedback_frame = tk.Frame(content_frame, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
            feedback_frame.pack(fill=tk.X, pady=10)
            
            # Header
            header_frame = tk.Frame(feedback_frame, bg='#2a2a2a')
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            
            timestamp = datetime.fromisoformat(feedback['timestamp'])
            time_str = timestamp.strftime("%d %b %Y, %I:%M %p")
            
            tk.Label(header_frame, text=f"From: {feedback['user_name']}", 
                    font=('Arial', 12, 'bold'), bg='#2a2a2a', fg='white').pack(side=tk.LEFT)
            tk.Label(header_frame, text=time_str, 
                    font=('Arial', 10), bg='#2a2a2a', fg='#888').pack(side=tk.RIGHT)
            
            # Feedback text
            tk.Label(feedback_frame, text=feedback['text'], font=('Arial', 11), 
                    bg='#2a2a2a', fg='#ccc', wraplength=800, justify='left').pack(anchor='w', padx=10, pady=10)
            
            # Mark as read button
            tk.Button(feedback_frame, text="Mark as Read", bg='#4CAF50', fg='white',
                     font=('Arial', 10), command=lambda fid=feedback['feedback_id']: self.mark_feedback_read(fid)).pack(anchor='e', padx=10, pady=5)
    
    def mark_feedback_read(self, feedback_id):
        """Mark feedback as read"""
        db.execute_query(
            "UPDATE feedbacks SET read_flag = 1 WHERE feedback_id = ?",
            (feedback_id,)
        )
        self.refresh_page()


if __name__ == "__main__":
    root = tk.Tk()
    app = theatre_booking_app(root)
    root.mainloop()
