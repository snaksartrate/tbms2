"""
Database module for Theatre Booking Management System
Uses SQLite for local storage
Can be extended to use Supabase or REST API by replacing query functions
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'tbms.db')


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    ''')
    
    # Producers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS producers (
            producer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Movies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            actors_json TEXT,
            languages_json TEXT,
            duration_seconds INTEGER,
            viewer_rating TEXT,
            cover_image_path TEXT,
            genres_json TEXT,
            average_rating REAL DEFAULT 0,
            upload_date TEXT,
            FOREIGN KEY (producer_id) REFERENCES producers(producer_id)
        )
    ''')
    
    # Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            performers_json TEXT,
            venue TEXT,
            duration_seconds INTEGER,
            date TEXT,
            time TEXT,
            average_rating REAL DEFAULT 0,
            cover_image_path TEXT,
            genres_json TEXT,
            upload_date TEXT,
            FOREIGN KEY (host_id) REFERENCES producers(producer_id)
        )
    ''')
    
    # Theatres table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS theatres (
            theatre_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            name TEXT NOT NULL,
            hall_type TEXT NOT NULL,
            seating_schema_json TEXT
        )
    ''')
    
    # Scheduled screens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_screens (
            screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            theatre_id INTEGER NOT NULL,
            movie_id INTEGER,
            event_id INTEGER,
            screen_number INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            seat_map_json TEXT,
            price_economy REAL,
            price_central REAL,
            price_premium REAL,
            FOREIGN KEY (theatre_id) REFERENCES theatres(theatre_id),
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            screen_id INTEGER NOT NULL,
            seat TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            refunded_flag INTEGER DEFAULT 0,
            booking_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (screen_id) REFERENCES scheduled_screens(screen_id)
        )
    ''')
    
    # Employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            salary REAL NOT NULL,
            city TEXT NOT NULL,
            theatre TEXT NOT NULL
        )
    ''')
    
    # Feedbacks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            read_flag INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Watchlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER,
            event_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    ''')
    
    conn.commit()
    
    # Create admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password, role, name, email, balance)
            VALUES ('admin', 'admin123', 'admin', 'Administrator', 'admin@pqrentertainment.com', 0)
        ''')
        conn.commit()
    
    conn.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and return results"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    if fetch_one:
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    elif fetch_all:
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    else:
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id


def insert_demo_data():
    """Insert demo data for testing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Demo users
    demo_users = [
        ('user1', 'password', 'user', 'John Doe', 'john@example.com', 0),
        ('user2', 'password', 'user', 'Jane Smith', 'jane@example.com', 0),
    ]
    
    for user in demo_users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, role, name, email, balance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', user)
    
    conn.commit()
    conn.close()


# Initialize database on module import
if not os.path.exists(DB_PATH):
    init_database()
    insert_demo_data()
