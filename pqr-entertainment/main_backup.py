"""
Theatre Booking Management System - Main Application
PQR Entertainment PaaS Desktop Application

Entry point: main.py
Packaging: pyinstaller --onefile --noconsole main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from datetime import datetime
import json

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
        tk.Button(nav_frame, text="Forward →", command=self.go_forward, **btn_style).pack(side=tk.LEFT, padx=5)
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
        
        if show_search:
            search_frame = tk.Frame(header_frame, bg='#2a2a2a')
            search_frame.pack(side=tk.LEFT, padx=20, expand=True, fill=tk.X)
            
            self.search_var = tk.StringVar()
            search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                   font=('Arial', 12), width=40)
            search_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(search_frame, text="Search", bg='#444', fg='white',
                     command=self.perform_search).pack(side=tk.LEFT)
        
        if show_username and current_user:
            user_label = tk.Label(header_frame, text=f"Welcome, {current_user['name']}", 
                                 font=('Arial', 12), bg='#2a2a2a', fg='white')
            user_label.pack(side=tk.RIGHT, padx=20)
            
            logout_btn = tk.Button(header_frame, text="Logout", bg='#d32f2f', fg='white',
                                  command=self.logout)
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
            tk.Button(self.menu_overlay, text="📞 Customer Service", 
                     command=self.show_customer_service, **menu_style).pack(fill=tk.X)
            
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
            tk.Button(self.menu_overlay, text="🎭 Theatres", 
                     command=lambda: self.navigate_to('theatres'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎥 Movies", 
                     command=lambda: self.navigate_to('admin_movies'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎪 Events", 
                     command=lambda: self.navigate_to('admin_events'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="👥 Employees", 
                     command=lambda: self.navigate_to('employees'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="🎬 Producers/Hosts", 
                     command=lambda: self.navigate_to('producers'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📺 Screen Manager", 
                     command=lambda: self.navigate_to('screen_manager'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="📊 Analytics", 
                     command=lambda: self.navigate_to('admin_analytics'), **menu_style).pack(fill=tk.X)
            tk.Button(self.menu_overlay, text="💬 Feedback", 
                     command=lambda: self.navigate_to('admin_feedback'), **menu_style).pack(fill=tk.X)
        
        tk.Button(self.menu_overlay, text="🚪 Logout", 
                 command=self.logout, bg='#d32f2f', fg='white', 
                 font=('Arial', 12), pady=10).pack(side=tk.BOTTOM, fill=tk.X)
    
    def navigate_to(self, page_name):
        """Navigate to a specific page"""
        self.toggle_menu()  # Close menu
        
        # Add to navigation stack
        global current_role, admin_stack, producer_stack, user_stack
        if current_role == 'admin':
            admin_stack.append(page_name)
        elif current_role == 'producer':
            producer_stack.append(page_name)
        elif current_role == 'user':
            user_stack.append(page_name)
        
        # Route to appropriate page
        if page_name == 'user_home':
            self.show_user_home()
        elif page_name == 'user_profile':
            self.show_user_profile()
        elif page_name == 'my_bookings':
            self.show_my_bookings()
        elif page_name == 'booking_history':
            self.show_booking_history()
        elif page_name == 'watchlist':
            self.show_watchlist()
        elif page_name == 'wallet':
            self.show_wallet()
        elif page_name == 'feedback':
            self.show_feedback_form()
        elif page_name == 'producer_dashboard':
            self.show_producer_dashboard()
        elif page_name == 'add_content':
            self.show_add_content()
        elif page_name == 'producer_analytics':
            self.show_producer_analytics()
        elif page_name == 'admin_profile':
            self.show_admin_profile()
        elif page_name == 'cinema_halls':
            self.show_cinema_halls()
        elif page_name == 'admin_analytics':
            self.show_admin_analytics()
        elif page_name == 'admin_feedback':
            self.show_admin_feedback()
        # Add more routes as needed
    
    def go_back(self):
        """Navigate backward"""
        global current_role, admin_stack, producer_stack, user_stack
        stack = admin_stack if current_role == 'admin' else producer_stack if current_role == 'producer' else user_stack
        
        if len(stack) > 1:
            stack.pop()  # Remove current
            page = stack.pop()  # Get previous
            self.navigate_to(page)
    
    def go_forward(self):
        """Navigate forward - placeholder for now"""
        messagebox.showinfo("Info", "Forward navigation not implemented yet")
    
    def refresh_page(self):
        """Refresh current page"""
        global current_role, admin_stack, producer_stack, user_stack
        stack = admin_stack if current_role == 'admin' else producer_stack if current_role == 'producer' else user_stack
        
        if stack:
            page = stack[-1]
            stack.pop()
            self.navigate_to(page)
    
    def perform_search(self):
        """Perform search - placeholder"""
        query = self.search_var.get()
        messagebox.showinfo("Search", f"Searching for: {query}")
    
    def show_customer_service(self):
        """Show customer service contact"""
        messagebox.showinfo("Customer Service", 
                          "Contact us at:\ncustomerservice@pqrentertainment.com")
    
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
        """Show user homepage - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_search=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="User Homepage", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        tk.Label(content_frame, text="Browse movies and events", 
                font=('Arial', 14), bg='#1a1a1a', fg='#888').pack()
    
    def show_user_profile(self):
        """Show user profile page - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="User Profile", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_my_bookings(self):
        """Show bookings - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="My Bookings", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_booking_history(self):
        """Show booking history - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Booking History", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_watchlist(self):
        """Show watchlist - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Watchlist", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_wallet(self):
        """Show wallet - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Wallet", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
        
        tk.Label(content_frame, text=f"Balance: ₹{current_user['balance']}", 
                font=('Arial', 18), bg='#1a1a1a', fg='white').pack(pady=10)
    
    def show_feedback_form(self):
        """Show feedback form - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Feedback", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
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
    
    def show_add_content(self):
        """Show add content page - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Add Movie/Event", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_producer_analytics(self):
        """Show producer analytics - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Analytics", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    # ==================== ADMIN PAGES ====================
    
    def show_admin_profile(self):
        """Show admin profile - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_search=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Admin Dashboard", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_cinema_halls(self):
        """Show cinema halls management - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Cinema Halls", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_admin_analytics(self):
        """Show admin analytics - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Analytics", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)
    
    def show_admin_feedback(self):
        """Show admin feedback - placeholder"""
        self.clear_container()
        self.add_navigation_bar()
        self.add_header(show_menu=True, show_username=True)
        
        content_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="User Feedback", font=('Arial', 24, 'bold'),
                bg='#1a1a1a', fg='white').pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = theatre_booking_app(root)
    root.mainloop()
