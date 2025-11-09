# Theatre Booking Management System
## PQR Entertainment - PaaS Desktop Application

A comprehensive theatre booking management system built with Python and Tkinter.

---

## Features

### User Features
- Browse movies and events
- Search and filter by genre, language, rating
- Book tickets with seat selection
- Digital wallet for payments
- Watchlist management
- Booking history
- Submit feedback

### Producer/Host Features
- Upload and manage movies/events
- View analytics and ticket sales
- Edit content details
- Track performance metrics

### Admin Features
- Manage cinema halls and theatres
- Employee management
- Screen scheduling
- Review user feedback
- Comprehensive analytics dashboard

---

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Required packages: `tkinter` (usually included with Python), `sqlite3`

### Installation

1. Navigate to the project directory:
```bash
cd pqr-entertainment
```

2. Run the demo data population script (first time only):
```bash
python populate_demo_data.py
```

3. Run the application:
```bash
python main.py
```

---

## Project Structure

```
pqr-entertainment/
├── main.py                    # Main application entry point
├── database.py                # Database module (SQLite)
├── populate_demo_data.py      # Demo data population script
├── tbms.db                    # SQLite database file (auto-created)
├── assets/                    # Asset folder for images
└── README.md                  # This file
```

---

## Default Credentials

### Admin
- **Username:** admin
- **Password:** admin123

### Demo Users
- **Username:** user1 / user2
- **Password:** password

### Demo Producer
- **Username:** producer1
- **Password:** password

---

## Database Schema

### Tables
- **users** - User accounts (all roles)
- **producers** - Producer/host information
- **movies** - Movie catalog
- **events** - Events/shows catalog
- **theatres** - Cinema halls and stage theatres
- **scheduled_screens** - Movie/event schedules
- **bookings** - User bookings
- **employees** - Employee records
- **feedbacks** - User feedback
- **watchlist** - User watchlists

---

## Navigation System

The application features a comprehensive navigation system with:
- **Forward/Backward navigation** - Navigate through page history
- **Refresh button** - Reload current page data
- **Hamburger menu** - Role-based quick access menu
- **Navigation stacks** - Separate stacks for each user role

---

## Cities Supported

- Mumbai
- Pune
- Nashik
- Bangalore

Each city has:
- 4 Cinema halls (5 screens each)
- 1 Theatre/Stage hall (5 screens each)

---

## Seat Layout

### Cinema Halls
- **10x10 seat matrix** (100 seats)
- **Rows:** A-J (bottom to top)
- **Columns:** 1-10 (left to right)
- **Sections:**
  - Economy: Rows A-C (₹150-200)
  - Central: Rows D-G (₹200-250)
  - Recliner: Rows H-J (₹300-350)

### Theatre/Stage Halls
- **10x10 seat matrix** (100 seats)
- **Sections:**
  - Economy: Rows H-J (top 3)
  - Central: Rows D-G (middle 4)
  - Premium: Rows A-C (bottom 3)

---

## Packaging for Distribution

### Using PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --noconsole main.py

# The executable will be in the dist/ folder
```

### Using cx_Freeze

```bash
# Install cx_Freeze
pip install cx-freeze

# Create setup.py and build
python setup.py build
```

### Notes for Packaging
- Include the `assets/` folder with the executable
- The database file (`tbms.db`) will be created automatically
- Ensure all required images are in the `assets/` folder (see `provide-these.txt`)

---

## Extension to Cloud Backend

The application is designed to easily migrate to a cloud backend:

### Current: SQLite (Local)
```python
# database.py uses local SQLite
conn = sqlite3.connect('tbms.db')
```

### Future: Supabase / REST API
Replace the `execute_query()` function in `database.py` with API calls:

```python
import requests

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    # Convert SQL to REST API calls
    response = requests.post('https://api.example.com/query', 
                           json={'query': query, 'params': params})
    return response.json()
```

---

## Development Roadmap

### Phase 1: Core Features ✓
- [x] Authentication system
- [x] Database schema
- [x] Navigation system
- [x] Basic UI structure

### Phase 2: User Features (In Progress)
- [ ] Complete user homepage with movie cards
- [ ] Booking flow with seat selection
- [ ] Wallet functionality
- [ ] Watchlist implementation
- [ ] Feedback system

### Phase 3: Producer Features
- [ ] Content upload forms
- [ ] Analytics dashboard
- [ ] Content management

### Phase 4: Admin Features
- [ ] Theatre management
- [ ] Employee management
- [ ] Screen scheduling
- [ ] Feedback review
- [ ] Admin analytics

### Phase 5: Polish
- [ ] Add all cover images
- [ ] Implement search and filters
- [ ] Add testimonials
- [ ] Performance optimization

---

## Known Limitations

1. **Assets:** Movie/event cover images need to be provided (see `provide-these.txt` in root directory)
2. **Forward Navigation:** Currently shows placeholder message
3. **Payment Gateway:** Uses wallet balance only (no external gateway integration)
4. **Email:** No actual email sending (display only)

---

## Contributing

This is a lab project for PQR Entertainment. Contact the development team for contributions.

---

## License

Proprietary - PQR Entertainment © 2025

---

## Contact

- **Customer Service:** customerservice@pqrentertainment.com
- **General Contact:** contact@pqrentertainment.com
- **Admin:** admin@pqrentertainment.com
