"""
Populate database with demo data for testing
Run this script to add sample movies, events, theatres, and schedules
"""

import database as db
import json
from datetime import datetime, timedelta

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
            'id': 7,
            'title': 'Tumhari Sulu',
            'description': 'A happy-go-lucky Mumbai suburban housewife Sulochana takes up a job as a radio jockey, which leads to unexpected and transformational changes in her life.',
            'actors': ['Vidya Balan', 'Manav Kaul', 'Neha Dhupia'],
            'languages': ['Hindi', 'English'],
            'duration_seconds': 8400,
            'viewer_rating': 'U',
            'genres': ['Drama', 'Comedy'],
            'average_rating': 4.2,
            'producer_id': 'tanujGarg'
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
    
    # Update provide-these.txt with image requirements
    with open('../provide-these.txt', 'w') as f:
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
    
    # Update provide-these.txt
    with open('../provide-these.txt', 'a') as f:
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
    
    # Create schedules for next 3 days
    for day_offset in range(4):  # Today + next 3 days
        date = datetime.now() + timedelta(days=day_offset)
        
        for theatre in theatres:
            # Schedule different movies on different screens
            for screen_num in range(1, 6):  # 5 screens
                movie_idx = (screen_num + day_offset) % len(movies)
                movie_id = movies[movie_idx]['movie_id']
                
                # Morning show
                start_time = date.replace(hour=10, minute=0, second=0).isoformat()
                end_time = date.replace(hour=13, minute=0, second=0).isoformat()
                
                # Initialize empty seat map (all available)
                seat_map = [[0 for _ in range(10)] for _ in range(10)]
                
                db.execute_query(
                    """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number, 
                       start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (theatre['theatre_id'], movie_id, screen_num, start_time, end_time,
                     json.dumps(seat_map), 150.0, 200.0, 300.0)
                )
                
                # Afternoon show
                start_time = date.replace(hour=14, minute=30, second=0).isoformat()
                end_time = date.replace(hour=17, minute=30, second=0).isoformat()
                
                db.execute_query(
                    """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number,
                       start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (theatre['theatre_id'], movie_id, screen_num, start_time, end_time,
                     json.dumps(seat_map), 150.0, 200.0, 300.0)
                )
                
                # Evening show
                start_time = date.replace(hour=19, minute=0, second=0).isoformat()
                end_time = date.replace(hour=22, minute=0, second=0).isoformat()
                
                db.execute_query(
                    """INSERT INTO scheduled_screens (theatre_id, movie_id, screen_number,
                       start_time, end_time, seat_map_json, price_economy, price_central, price_premium)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (theatre['theatre_id'], movie_id, screen_num, start_time, end_time,
                     json.dumps(seat_map), 200.0, 250.0, 350.0)
                )
    
    print("✓ Scheduled screens populated")


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


if __name__ == "__main__":
    print("Populating demo data...")
    populate_theatres()
    populate_demo_producer_and_movies()
    populate_demo_events()
    populate_scheduled_screens()
    populate_employees()
    print("\n✓ All demo data populated successfully!")
