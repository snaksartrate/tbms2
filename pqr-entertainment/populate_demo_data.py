"""
Populate database with demo data for testing
Run this script to add sample movies, events, theatres, and schedules
"""

from dbwrap import db
import json
from datetime import datetime, timedelta
import os
import random

def populate_theatres():
    """Populate theatres from database/cities/theatres/theatres.json"""
    # Load theatre data from JSON
    theatres_data = [
        {"theatre_id": 1, "theatre_name": "PVR Phoenix", "city": "Mumbai", "3d": True, "imax": True},
        {"theatre_id": 2, "theatre_name": "INOX Palladium", "city": "Mumbai", "3d": True, "imax": False},
        {"theatre_id": 3, "theatre_name": "Cinepolis Andheri", "city": "Mumbai", "3d": False, "imax": True},
        {"theatre_id": 4, "theatre_name": "Carnival Cinemas", "city": "Mumbai", "3d": False, "imax": False},
        {"theatre_id": 5, "theatre_name": "City Pride", "city": "Nashik", "3d": True, "imax": True},
        {"theatre_id": 6, "theatre_name": "Z Square Mall", "city": "Nashik", "3d": True, "imax": False},
        {"theatre_id": 7, "theatre_name": "Inorbit Mall", "city": "Nashik", "3d": False, "imax": True},
        {"theatre_id": 8, "theatre_name": "Apsara Theatre", "city": "Nashik", "3d": False, "imax": False},
        {"theatre_id": 9, "theatre_name": "INOX Bund Garden", "city": "Pune", "3d": True, "imax": True},
        {"theatre_id": 10, "theatre_name": "PVR Pavilion", "city": "Pune", "3d": True, "imax": False},
        {"theatre_id": 11, "theatre_name": "E-Square Cinemas", "city": "Pune", "3d": False, "imax": True},
        {"theatre_id": 12, "theatre_name": "Seasons Mall", "city": "Pune", "3d": False, "imax": False},
        {"theatre_id": 13, "theatre_name": "PVR Forum", "city": "Bangalore", "3d": True, "imax": True},
        {"theatre_id": 14, "theatre_name": "INOX Garuda", "city": "Bangalore", "3d": True, "imax": False},
        {"theatre_id": 15, "theatre_name": "Cinepolis Royal", "city": "Bangalore", "3d": False, "imax": True},
        {"theatre_id": 16, "theatre_name": "Mantri Square", "city": "Bangalore", "3d": False, "imax": False},
    ]
    # Add one stage hall per city
    stage_halls = [
        ("Mumbai",  "Royal Opera House"),
        ("Nashik",  "Kalidas Rangmandir"),
        ("Pune",    "Tilak Smarak Mandir"),
        ("Bangalore","Rangashankara"),
    ]
    for city, name in stage_halls:
        schema = {
            'screens': 5,
            'seats_per_screen': 100,
            '3d': False,
            'imax': False,
        }
        db.execute_query(
            "INSERT INTO theatres (city, name, hall_type, seating_schema_json) VALUES (?, ?, ?, ?)",
            (city, name, 'stage', json.dumps(schema))
        )
    
    for theatre in theatres_data:
        schema = {
            'screens': 5, 
            'seats_per_screen': 100,
            '3d': theatre['3d'],
            'imax': theatre['imax']
        }
        db.execute_query(
            "INSERT INTO theatres (city, name, hall_type, seating_schema_json) VALUES (?, ?, ?, ?)",
            (theatre['city'], theatre['theatre_name'], 'cinema', json.dumps(schema))
        )
    
    print("✓ Theatres populated")


def populate_demo_producer_and_movies():
    """Create demo producer and movies"""
    # Create demo producer
    producer_user_id = db.execute_query(
        "INSERT OR IGNORE INTO users (username, password, role, name, email, balance) VALUES (?, ?, ?, ?, ?, 0)",
        ('producer1', 'password', 'producer', 'Demo Producer', 'producer@example.com')
    )
    
    if producer_user_id:
        producer_id = db.execute_query(
            "INSERT INTO producers (user_id, name, details) VALUES (?, ?, ?)",
            (producer_user_id, 'Demo Producer', 'Award-winning film producer')
        )
    else:
        # Get existing producer
        user = db.execute_query(
            "SELECT user_id FROM users WHERE username = 'producer1'",
            fetch_one=True
        )
        producer = db.execute_query(
            "SELECT producer_id FROM producers WHERE user_id = ?",
            (user['user_id'],), fetch_one=True
        )
        producer_id = producer['producer_id']
    
    # Demo movies - All 16 films from database/movies
    movies = [
        {
            'id': 1,
            'title': 'Inception',
            'description': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into someone\'s mind.',
            'actors': ['Leonardo DiCaprio', 'Marion Cotillard', 'Tom Hardy'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 8880,
            'viewer_rating': 'PG-13',
            'genres': ['Sci-Fi', 'Thriller'],
            'average_rating': 4.8,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 2,
            'title': 'Interstellar',
            'description': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
            'actors': ['Matthew McConaughey', 'Anne Hathaway', 'Jessica Chastain'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 10140,
            'viewer_rating': 'PG-13',
            'genres': ['Sci-Fi', 'Drama'],
            'average_rating': 4.7,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 3,
            'title': 'The Prestige',
            'description': 'Two stage magicians engage in competitive one-upmanship in an attempt to create the ultimate stage illusion.',
            'actors': ['Christian Bale', 'Hugh Jackman', 'Scarlett Johansson'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 7800,
            'viewer_rating': 'PG-13',
            'genres': ['Mystery', 'Drama'],
            'average_rating': 4.6,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 4,
            'title': 'Batman Begins',
            'description': 'After training with his mentor, Batman begins his fight to free crime-ridden Gotham City from corruption.',
            'actors': ['Christian Bale', 'Michael Caine', 'Liam Neeson'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 8400,
            'viewer_rating': 'PG-13',
            'genres': ['Action', 'Adventure'],
            'average_rating': 4.5,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 5,
            'title': 'The Dark Knight',
            'description': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest tests.',
            'actors': ['Christian Bale', 'Heath Ledger', 'Aaron Eckhart'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 9120,
            'viewer_rating': 'PG-13',
            'genres': ['Action', 'Crime'],
            'average_rating': 4.9,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 6,
            'title': 'The Dark Knight Rises',
            'description': 'Eight years after the Joker\'s reign of anarchy, Batman is forced from exile to save Gotham City from the terrorist Bane.',
            'actors': ['Christian Bale', 'Tom Hardy', 'Anne Hathaway'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 9900,
            'viewer_rating': 'PG-13',
            'genres': ['Action', 'Thriller'],
            'average_rating': 4.6,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 8,
            'title': 'Drishyam',
            'description': 'A man goes to extreme lengths to save his family from punishment after the family commits an accidental crime.',
            'actors': ['Ajay Devgn', 'Tabu', 'Shriya Saran'],
            'languages': ['Hindi', 'Malayalam'],
            'duration_seconds': 9780,
            'viewer_rating': 'U/A',
            'genres': ['Crime', 'Drama'],
            'average_rating': 4.5,
            'producer_id': 'kumarMangat'
        },
        {
            'id': 9,
            'title': 'Drishyam 2',
            'description': 'Seven years after the case related to Vijay\'s family was closed, a series of unexpected events bring a new investigation and truth to unfold.',
            'actors': ['Ajay Devgn', 'Tabu', 'Akshaye Khanna'],
            'languages': ['Hindi', 'Malayalam'],
            'duration_seconds': 8400,
            'viewer_rating': 'U/A',
            'genres': ['Crime', 'Thriller'],
            'average_rating': 4.4,
            'producer_id': 'kumarMangat'
        },
        {
            'id': 10,
            'title': 'Dune',
            'description': 'Feature adaptation of Frank Herbert\'s science fiction novel about the son of a noble family entrusted with the protection of the most valuable asset in the galaxy.',
            'actors': ['Timothée Chalamet', 'Rebecca Ferguson', 'Oscar Isaac'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 9300,
            'viewer_rating': 'PG-13',
            'genres': ['Sci-Fi', 'Adventure'],
            'average_rating': 4.5,
            'producer_id': 'denisVilleneuve'
        },
        {
            'id': 11,
            'title': 'Dune: Part Two',
            'description': 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.',
            'actors': ['Timothée Chalamet', 'Zendaya', 'Rebecca Ferguson'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 9960,
            'viewer_rating': 'PG-13',
            'genres': ['Sci-Fi', 'Adventure'],
            'average_rating': 4.7,
            'producer_id': 'denisVilleneuve'
        },
        {
            'id': 12,
            'title': 'Fight Club',
            'description': 'An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.',
            'actors': ['Brad Pitt', 'Edward Norton', 'Helena Bonham Carter'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 8340,
            'viewer_rating': 'R',
            'genres': ['Drama', 'Thriller'],
            'average_rating': 4.7,
            'producer_id': 'davidFincher'
        },
        {
            'id': 13,
            'title': 'Kantara',
            'description': 'A fiery action thriller about a small-time Kambla champion who is at loggerheads with an upright forest officer.',
            'actors': ['Rishab Shetty', 'Sapthami Gowda', 'Kishore Kumar G.'],
            'languages': ['Kannada', 'Hindi', 'Tamil', 'Telugu'],
            'duration_seconds': 8880,
            'viewer_rating': 'U/A',
            'genres': ['Action', 'Drama'],
            'average_rating': 4.6,
            'producer_id': 'vijayKiragandur'
        },
        {
            'id': 14,
            'title': 'Memento',
            'description': 'A man with short-term memory loss attempts to track down his wife\'s murderer.',
            'actors': ['Guy Pearce', 'Carrie-Anne Moss', 'Joe Pantoliano'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 6780,
            'viewer_rating': 'R',
            'genres': ['Mystery', 'Thriller'],
            'average_rating': 4.7,
            'producer_id': 'christopherNolan'
        },
        {
            'id': 15,
            'title': 'The Godfather',
            'description': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.',
            'actors': ['Marlon Brando', 'Al Pacino', 'James Caan'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 10500,
            'viewer_rating': 'R',
            'genres': ['Crime', 'Drama'],
            'average_rating': 4.9,
            'producer_id': 'francisFordCoppola'
        },
        {
            'id': 16,
            'title': 'Tenet',
            'description': 'Armed with only one word, Tenet, and fighting for the survival of the entire world, the Protagonist journeys through a twilight world of international espionage.',
            'actors': ['John David Washington', 'Robert Pattinson', 'Elizabeth Debicki'],
            'languages': ['English', 'Hindi'],
            'duration_seconds': 9000,
            'viewer_rating': 'PG-13',
            'genres': ['Action', 'Sci-Fi'],
            'average_rating': 4.4,
            'producer_id': 'christopherNolan'
        },
    ]
    
    for movie in movies:
        db.execute_query(
            """INSERT INTO movies (producer_id, title, description, actors_json, languages_json, 
               duration_seconds, viewer_rating, cover_image_path, genres_json, average_rating, upload_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (producer_id, movie['title'], movie['description'], json.dumps(movie['actors']),
             json.dumps(movie['languages']), movie['duration_seconds'], movie['viewer_rating'],
             f"assets/{movie['title'].lower().replace(' ', '_').replace(':', '')}.jpg",
             json.dumps(movie['genres']), movie['average_rating'], datetime.now().isoformat())
        )
    
    # Update provide-these.txt with image requirements (inside pqr-entertainment)
    assets_req_path = os.path.join(os.path.dirname(__file__), 'provide-these.txt')
    with open(assets_req_path, 'w') as f:
        f.write('# Asset Requirements for Theatre Booking Management System\n')
        f.write('# Place all assets in pqr-entertainment/assets/ folder\n\n')
        f.write('# Movie Cover Images\n')
        for movie in movies:
            filename = f"{movie['title'].replace(' ', '_').replace(':', '')}.jpg"
            f.write(f"{filename} - Cover image for movie {movie['title']}\n")
    
    print("✓ Movies populated and assets logged")


def populate_demo_events():
    """Create demo events"""
    # Get producer
    user = db.execute_query(
        "SELECT user_id FROM users WHERE username = 'producer1'",
        fetch_one=True
    )
    if not user:
        return
    
    producer = db.execute_query(
        "SELECT producer_id FROM producers WHERE user_id = ?",
        (user['user_id'],), fetch_one=True
    )
    if not producer:
        return
    
    host_id = producer['producer_id']
    
    # Demo events
    events = [
        {
            'title': 'Rock Night Live',
            'description': 'An electrifying rock concert featuring top bands from around the country.',
            'performers': ['The Rockers', 'Thunder Storm', 'Echo Valley'],
            'venue': 'Grand Theatre',
            'duration_seconds': 10800,  # 3h
            'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'time': '19:00:00',
            'genres': ['Music', 'Rock', 'Live Performance'],
            'average_rating': 4.3
        },
        {
            'title': 'Stand-Up Comedy Night',
            'description': 'Laugh out loud with the best comedians performing their latest acts.',
            'performers': ['John Doe', 'Jane Hilarious', 'Comedy King'],
            'venue': 'Grand Theatre',
            'duration_seconds': 7200,  # 2h
            'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'time': '20:00:00',
            'genres': ['Comedy', 'Live Performance'],
            'average_rating': 4.2
        },
    ]
    
    for event in events:
        db.execute_query(
            """INSERT INTO events (host_id, title, description, performers_json, venue,
               duration_seconds, date, time, cover_image_path, genres_json, average_rating, upload_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (host_id, event['title'], event['description'], json.dumps(event['performers']),
             event['venue'], event['duration_seconds'], event['date'], event['time'],
             f"assets/{event['title'].lower().replace(' ', '_')}.jpg",
             json.dumps(event['genres']), event['average_rating'], datetime.now().isoformat())
        )
    
    # Update provide-these.txt (inside pqr-entertainment)
    assets_req_path = os.path.join(os.path.dirname(__file__), 'provide-these.txt')
    with open(assets_req_path, 'a') as f:
        f.write('\n# Event Cover Images\n')
        for event in events:
            filename = f"{event['title'].replace(' ', '_')}.jpg"
            f.write(f"{filename} - Cover image for event {event['title']}\n")
    
    print("✓ Events populated and assets logged")


def populate_scheduled_screens():
    """Create scheduled screens for next 3 days"""
    # Get all movies
    movies = db.execute_query("SELECT movie_id FROM movies", fetch_all=True)
    
    # Get all cinema theatres
    theatres = db.execute_query(
        "SELECT theatre_id, city, name FROM theatres WHERE hall_type = 'cinema'",
        fetch_all=True
    )
    
    # Create base schedules for next 3 days (existing logic)
    for day_offset in range(4):  # Today + next 3 days
        date = datetime.now() + timedelta(days=day_offset)
        for theatre in theatres:
            for screen_num in range(1, 5+1):  # 5 screens
                movie_idx = (screen_num + day_offset) % len(movies)
                movie_id = movies[movie_idx]['movie_id']
                # Morning/Afternoon/Evening
                seat_map = [[0 for _ in range(10)] for _ in range(10)]
                for st, et, pe, pc, pp in [
                    ((10,0,0), (13,0,0), 150.0, 200.0, 300.0),
                    ((14,30,0), (17,30,0), 150.0, 200.0, 300.0),
                    ((19,0,0), (22,0,0), 200.0, 250.0, 350.0),
                ]:
                    start_time = date.replace(hour=st[0], minute=st[1], second=st[2]).isoformat()
                    end_time = date.replace(hour=et[0], minute=et[1], second=et[2]).isoformat()
                    db.execute_query(
                        """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number,
                           start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (theatre['theatre_id'], movie_id, screen_num, start_time, end_time,
                         json.dumps(seat_map), pe, pc, pp)
                    )

    # Coverage step: ensure every movie appears in every city each day (at least one show)
    cities = sorted({t['city'] for t in theatres})
    timeslots = [(12, 0, 0), (16, 0, 0), (20, 0, 0)]  # fallback times
    for day_offset in range(4):
        date = datetime.now() + timedelta(days=day_offset)
        for city in cities:
            city_theatres = [t for t in theatres if t['city'] == city]
            if not city_theatres:
                continue
            for mi, m in enumerate(movies):
                # Check if any show exists for this movie in this city on this date
                existing = db.execute_query(
                    """
                    SELECT 1 FROM scheduled_screens ss
                    JOIN theatres t ON ss.theatre_id = t.theatre_id
                    WHERE t.city = ? AND ss.movie_id = ? AND DATE(ss.start_time) = DATE(?)
                    LIMIT 1
                    """,
                    (city, m['movie_id'], date.isoformat()), fetch_one=True
                )
                if existing:
                    continue
                # Insert a single show for coverage
                theatre = city_theatres[mi % len(city_theatres)]
                screen_num = (mi % 5) + 1
                h, mn, s = timeslots[mi % len(timeslots)]
                start_time = date.replace(hour=h, minute=mn, second=s)
                end_time = start_time + timedelta(hours=3)
                seat_map = [[0 for _ in range(10)] for _ in range(10)]
                db.execute_query(
                    """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number,
                       start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (theatre['theatre_id'], m['movie_id'], screen_num, start_time.isoformat(), end_time.isoformat(),
                     json.dumps(seat_map), 150.0, 220.0, 320.0)
                )
    print("✓ Scheduled screens populated (all movies covered in each city)")


def populate_employees():
    """Populate employee data"""
    cities = ['Mumbai', 'Pune', 'Nashik', 'Bangalore']
    designations = ['Manager', 'Usher', 'Ticket Counter Staff', 'Projectionist', 'Cleaner']
    
    theatres_data = db.execute_query("SELECT name, city FROM theatres", fetch_all=True)
    
    for theatre in theatres_data[:10]:  # Add employees for first 10 theatres
        for designation in designations:
            salary = {
                'Manager': 50000,
                'Usher': 20000,
                'Ticket Counter Staff': 25000,
                'Projectionist': 35000,
                'Cleaner': 15000
            }[designation]
            
            db.execute_query(
                """INSERT INTO employees (name, designation, salary, city, theatre)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Employee {designation}", designation, salary, theatre['city'], theatre['name'])
            )
    
    print("✓ Employees populated")


def populate_users():
    """Create multiple demo users with balances (idempotent by username)"""
    users = [
        ('alice', 'password', 'user', 'Alice Johnson', 'alice@example.com', 1500),
        ('bob', 'password', 'user', 'Bob Martin', 'bob@example.com', 1200),
        ('carol', 'password', 'user', 'Carol Peters', 'carol@example.com', 800),
        ('dave', 'password', 'user', 'Dave Singh', 'dave@example.com', 500),
        ('emma', 'password', 'user', 'Emma Watson', 'emma@example.com', 2000),
        ('frank', 'password', 'user', 'Frank Castle', 'frank@example.com', 300),
        ('grace', 'password', 'user', 'Grace Lee', 'grace@example.com', 900),
        ('henry', 'password', 'user', 'Henry Ford', 'henry@example.com', 1100),
    ]
    for u in users:
        db.execute_query(
            "INSERT OR IGNORE INTO users (username, password, role, name, email, balance) VALUES (?, ?, ?, ?, ?, ?)",
            u
        )
    print("✓ Users populated")


def populate_event_schedules():
    """Create scheduled screens for events in various theatres and dates"""
    events = db.execute_query("SELECT event_id FROM events", fetch_all=True)
    if not events:
        print("! No events to schedule")
        return
    theatres = db.execute_query(
        "SELECT theatre_id FROM theatres WHERE hall_type = 'stage'",
        fetch_all=True
    )
    if not theatres:
        print("! No theatres found for events")
        return
    for day_offset in range(1, 5):
        date = datetime.now() + timedelta(days=day_offset)
        for th in theatres[:6]:  # a subset to avoid explosion
            for idx, ev in enumerate(events[:3]):  # few events per theatre
                start_dt = date.replace(hour=18 + (idx % 3)*2, minute=0, second=0)
                end_dt = start_dt + timedelta(hours=2)
                start_time = start_dt.isoformat()
                end_time = end_dt.isoformat()
                seat_map = [[0 for _ in range(10)] for _ in range(10)]
                db.execute_query(
                    """INSERT INTO scheduled_screens (theatre_id, event_id, screen_number, start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (th['theatre_id'], ev['event_id'], (idx % 5) + 1, start_time, end_time, json.dumps(seat_map), 200.0, 300.0, 450.0)
                )
    print("✓ Event schedules populated")


def populate_random_bookings():
    """Generate random bookings with limited volume for speed; update seat maps with progress logs"""
    users = db.execute_query("SELECT user_id, balance FROM users WHERE role='user'", fetch_all=True)
    screens = db.execute_query("SELECT screen_id, seat_map_json, price_economy, price_central, price_premium FROM scheduled_screens", fetch_all=True)
    if not users or not screens:
        print("! Skipped bookings (no users or screens)")
        return
    # Limit processed screens to keep runtime reasonable
    max_screens = min(250, len(screens))
    screens = screens[:max_screens]
    for idx, s in enumerate(screens, start=1):
        # pick 3-8 seats to book
        to_book = random.randint(3, 8)
        try:
            seat_map = json.loads(s['seat_map_json'])
        except:
            seat_map = [[0 for _ in range(10)] for _ in range(10)]
        booked_now = 0
        attempts = 0
        while booked_now < to_book and attempts < 80:
            attempts += 1
            r = random.randint(0,9)
            c = random.randint(0,9)
            if seat_map[r][c] == 1:
                continue
            # determine price based on row as per UI logic
            if r < 3:
                price = s['price_premium'] or 400
            elif r < 7:
                price = s['price_central'] or 300
            else:
                price = s['price_economy'] or 200
            seat_label = chr(ord('J') - r) + str(c+1)
            user = random.choice(users)
            # insert booking, do not enforce wallet deduction here (demo data)
            when = datetime.now() - timedelta(days=random.randint(0, 14))
            db.execute_query(
                """INSERT INTO bookings (user_id, screen_id, seat, amount, status, refunded_flag, booking_date)
                       VALUES (?, ?, ?, ?, 'confirmed', 0, ?)""",
                (user['user_id'], s['screen_id'], seat_label, float(price), when.isoformat())
            )
            seat_map[r][c] = 1
            booked_now += 1
        # update seat map
        db.execute_query("UPDATE scheduled_screens SET seat_map_json = ? WHERE screen_id = ?", (json.dumps(seat_map), s['screen_id']))
        if idx % 50 == 0 or idx == max_screens:
            print(f"  - Bookings progress: {idx}/{max_screens} screens updated")
    print("✓ Random bookings populated and seat maps updated")


def populate_watchlists_and_feedbacks():
    """Add random watchlist entries and feedback messages"""
    users = db.execute_query("SELECT user_id FROM users WHERE role='user'", fetch_all=True)
    movies = db.execute_query("SELECT movie_id FROM movies", fetch_all=True)
    events = db.execute_query("SELECT event_id FROM events", fetch_all=True)
    if users:
        for u in users:
            # 3 random movies and 2 random events
            for m in random.sample(movies, min(3, len(movies))):
                db.execute_query("INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)", (u['user_id'], m['movie_id']))
            for e in random.sample(events, min(2, len(events))):
                db.execute_query("INSERT INTO watchlist (user_id, event_id) VALUES (?, ?)", (u['user_id'], e['event_id']))
            # feedback
            if random.random() < 0.6:
                msg = random.choice([
                    "Great experience!",
                    "Could improve seat spacing",
                    "Loved the UI and quick booking",
                    "Payment was smooth",
                    "Please add more shows in my city",
                ])
                db.execute_query(
                    "INSERT INTO feedbacks (user_id, text, timestamp, read_flag) VALUES (?, ?, ?, 0)",
                    (u['user_id'], msg, datetime.now().isoformat())
                )
    print("✓ Watchlists and feedbacks populated")


if __name__ == "__main__":
    print("Populating demo data...")
    populate_theatres()
    populate_users()
    populate_demo_producer_and_movies()
    populate_demo_events()
    populate_scheduled_screens()
    populate_event_schedules()
    populate_random_bookings()
    populate_employees()
    populate_watchlists_and_feedbacks()
    print("\n✓ All demo data populated successfully!")
