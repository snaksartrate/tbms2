# Theatre Booking Management System - Completion Plan

## Current Status (Updated)

### ✅ Completed
1. **Database Schema** - All 10 tables created with proper relationships
2. **Authentication System** - Login, registration for all roles
3. **Navigation Framework** - Stacks, forward/back/refresh buttons
4. **Menu System** - Role-based hamburger menu
5. **Demo Data** - All 16 movies from database/movies, 16 theatres from database/cities
6. **Project Structure** - Proper folder organization
7. **Asset Tracking** - provide-these.txt updated with all 16 movies + 2 events

### ⚙️ In Progress
- Page placeholders for all roles
- Basic UI framework

### ⏳ Pending
- Full user features (booking, wallet, watchlist, profile updates)
- Producer dashboard and content management
- Admin CRUD operations
- Analytics dashboards

---

## Completion Strategy

I'll complete this project in **5 focused phases**, prioritizing user-facing features first since they demonstrate the core value proposition.

---

## Phase 1: Core User Experience (Priority: CRITICAL)
**Estimated Time: 6-8 hours**

### 1.1 User Homepage (2-3 hours)
**Files to modify:** `main.py` (show_user_home method)

**Implementation:**
```python
- Create scrollable canvas for content
- Add genre filter dropdown (extract unique genres from DB)
- Implement search functionality (query movies by title)
- Movie card grid (4 per row):
  - Display cover image (or placeholder if missing)
  - Show title, rating, languages
  - Click handler to show movie details
- Banner section:
  - Rotating carousel (2 featured movies)
  - Auto-rotate every 10 seconds
  - Left and right carousel controls
- Testimonials section:
  - 10 hardcoded testimonials
  - Rotate 3 at a time every 10 seconds
- Footer with contact info
```

**Key Functions Needed:**
- `load_movies_grid()` - Fetch and display movies
- `create_movie_card(movie_data)` - Create individual card widgets
- `show_movie_detail(movie_id)` - Popup/new page with full details
- `apply_filters()` - Filter movies by genre/language
- `search_movies(query)` - Search implementation

### 1.2 Movie Detail Page & Booking Flow (3-4 hours)
**New methods:** `show_movie_detail()`, `show_city_selection()`, `show_theatre_listing()`, `show_seat_selection()`

**Implementation:**
```python
# Movie Detail Page:
- Cover image (large)
- Title, description, cast, genres, languages, duration, rating
- "Add to Watchlist" button (toggle)
- "Book Tickets" button → triggers booking flow

# Booking Flow:
Step 1: City Selection Popup
- 4 buttons: Mumbai, Pune, Nashik, Bangalore
- On selection → query theatres in that city showing this movie

Step 2: Theatre Listing
- List all theatres with available screens
- For each theatre:
  - Theatre name, 3D/IMAX badges
  - Expandable dropdown showing showtimes (today + 3 days)
  - Format: "10:00 AM - Economy ₹150, Central ₹200, Recliner ₹300"
- Click showtime → go to seat selection

Step 3: Seat Selection (CRITICAL)
- Display screen label at top
- 10x10 seat matrix (rows A-J, columns 1-10)
- Color coding:
  - Grey = booked (from seat_map_json)
  - White/light = available
  - Green = selected by user
- Section labels and prices:
  - Cinema: Economy (A-C), Central (D-G), Recliner (H-J)
  - Stage: Economy (H-J), Central (D-G), Premium (A-C)
- Allow multiple seat selection
- Show total price dynamically
- "Proceed to Payment" button

Step 4: Payment & Confirmation
- Show selected seats, theatre, time, total
- Check wallet balance
- If sufficient: deduct, create booking entries, update seat_map
- If insufficient: show "Can't book, you're broke."
- On success: show booking confirmation with booking ID
```

**Key Database Operations:**
```python
# Get screens for movie in city
SELECT ss.*, t.name, t.city FROM scheduled_screens ss
JOIN theatres t ON ss.theatre_id = t.theatre_id
WHERE t.city = ? AND ss.movie_id = ?
AND DATE(ss.start_time) BETWEEN DATE('now') AND DATE('now', '+3 days')

# Check and update seats
- Parse seat_map_json
- Mark selected seats as booked
- Update scheduled_screens.seat_map_json
- Insert booking records (one per seat)
- Update user balance
```

### 1.3 Wallet System (30 mins)
**File:** `main.py` (show_wallet method)

**Implementation:**
```python
- Display current balance (from current_user)
- "Add Balance" button opens popup:
  - Input field for amount
  - "Add ₹500", "Add ₹1000", "Add ₹2000" quick buttons
  - On submit: update users.balance
- Show recent transactions (from bookings table)
- Refresh display after updates
```

### 1.4 Watchlist (30 mins)
**File:** `main.py` (show_watchlist method)

**Implementation:**
```python
- Query watchlist table for current user
- Display table with columns:
  - Type (Movie/Event), Title, Rating, Languages
  - Visit button → show_movie_detail()
  - Remove button → DELETE from watchlist
- Empty state message if no items
- Refresh on add/remove
```

### 1.5 User Profile & Updates (1 hour)
**File:** `main.py` (show_user_profile method)

**Implementation:**
```python
- Display user info (name, email, username)
- Buttons:
  - "Update Username" → popup with validation
  - "Update Password" → popup with old/new/confirm fields
  - "View Booking History"
  - "View Wallet"

# Update Username Popup:
- Check if new username exists
- Update if available
- Show success/error message

# Update Password Popup:
- Verify old password matches
- Ensure new != old
- Confirm new password matches
- Update and show success
```

### 1.6 Booking History (30 mins)
**File:** `main.py` (show_booking_history, show_my_bookings methods)

**Implementation:**
```python
# Booking History:
- Query all bookings for user (past and future)
- Table: Movie/Event, Date, Time, City, Theatre, Screen, Seat, Amount
- Sortable by date

# My Bookings (active only):
- Filter for future bookings only
- Same table structure
- Option to cancel (if > 24h before show)
```

---

## Phase 2: Producer Features (Priority: HIGH)
**Estimated Time: 4-5 hours**

### 2.1 Producer Dashboard (1.5 hours)
**File:** `main.py` (show_producer_dashboard method)

**Implementation:**
```python
- Get producer_id from current_user
- Query movies/events WHERE producer_id = current_producer
- Display as grid of cards (similar to user home)
- Each card shows:
  - Cover image, title, rating, upload date
  - Click → show producer movie detail page
- Search and filter options:
  - By title, genre, language, rating, upload date
- "Upload New Movie/Event" button → show_add_content()
```

### 2.2 Add/Edit Movie/Event (2 hours)
**File:** `main.py` (show_add_content, show_edit_content methods)

**Implementation:**
```python
# Form Fields:
- Type selector: Movie / Event
- Title (required)
- Description (textarea)
- Cover image path (text input - log to provide-these.txt)
- Actors/Performers (comma-separated)
- Languages (multi-select or comma-separated)
- Genres (multi-select or comma-separated)
- Duration (HH:MM format, convert to seconds)
- Viewer Rating (dropdown: U, U/A, PG-13, R)

# On Submit:
- Validate all fields
- If image path provided and not in assets:
  - Append to provide-these.txt
- Insert into movies/events table
- Show success message
- Redirect to dashboard

# Edit Mode:
- Pre-fill form with existing data
- UPDATE instead of INSERT
- Delete button (with confirmation)
```

### 2.3 Producer Analytics (1.5 hours)
**File:** `main.py` (show_producer_analytics method)
**New dependency:** matplotlib

**Implementation:**
```python
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Queries needed:
- Total bookings per movie (for bar chart)
- Bookings over time (for line chart)
- Genre distribution (for donut chart)
- Average occupancy percentage (for semicircular gauge)

# Charts:
1. Bar Chart: Ticket sales per movie
2. Line Chart: Weekly/monthly booking trends
3. Donut Chart: Genre/language distribution
4. Semicircular Gauge: Average occupancy %

# Date range filter:
- Dropdown: Last 7 days, Last 30 days, Last 90 days, All time
- Movie filter: All movies or specific movie

# Display charts in grid layout (2x2)
```

---

## Phase 3: Admin Features (Priority: HIGH)
**Estimated Time: 5-6 hours**

### 3.1 Theatre Management (1.5 hours)
**File:** `main.py` (show_cinema_halls, show_theatres methods)

**Implementation:**
```python
# Theatre List Page:
- Group by city (Mumbai, Pune, Nashik, Bangalore)
- Each city shows its theatres in table:
  - Theatre Name, Hall Type, 3D, IMAX, Screens
  - Edit, Delete buttons

# Add Theatre Popup:
- City dropdown
- Theatre name
- Hall type: Cinema / Stage
- 3D checkbox, IMAX checkbox
- Number of screens

# Edit Theatre:
- Pre-fill form
- UPDATE theatres table

# Delete Theatre:
- Confirmation dialog
- Check for active schedules first
- If yes: warn user
- DELETE cascade or set inactive flag
```

### 3.2 Employee Management (1 hour)
**File:** `main.py` (show_employees method)

**Implementation:**
```python
# Employee List:
- Table: Name, Designation, Salary, City, Theatre
- Search and filter options
- Add, Edit, Delete buttons

# CRUD Operations:
- Add: Form with all fields
- Edit: Pre-filled form
- Delete: Confirmation dialog
- Standard INSERT/UPDATE/DELETE queries
```

### 3.3 Screen Manager (1.5 hours)
**File:** `main.py` (show_screen_manager method)

**Implementation:**
```python
# View Schedules:
- Filter by:
  - Date range
  - City
  - Theatre
  - Movie/Event
- Table showing:
  - Theatre, Screen, Movie/Event, Date, Time, Booked/Total Seats

# Add Schedule:
- Select theatre → screen number
- Select movie/event
- Date and time pickers
- Set prices (economy, central, premium)
- Create with empty seat_map

# Edit/Delete Schedule:
- Edit: Update time/price only (not movie/theatre)
- Delete: Only if no bookings exist
- Confirmation dialogs
```

### 3.4 Feedback Management (45 mins)
**File:** `main.py` (show_admin_feedback method)

**Implementation:**
```python
# Feedback Page:
- Query feedbacks WHERE read_flag = 0 ORDER BY timestamp DESC LIMIT 10
- Display each feedback:
  - User name, timestamp, feedback text
  - "Mark as Read" button

# On Mark as Read:
- UPDATE feedbacks SET read_flag = 1 WHERE feedback_id = ?
- Remove from display
- Show next unread

# Load More:
- Pagination to show older feedbacks
```

### 3.5 Admin Analytics (45 mins)
**File:** `main.py` (show_admin_analytics method)

**Implementation:**
```python
# Similar to producer analytics but system-wide:
- All movies/events combined
- Total bookings, revenue
- Theatre-wise performance
- City-wise distribution
- Employee statistics (count, total salary)

# Charts:
- Bar: Theatre-wise bookings
- Line: Daily/weekly booking trends
- Donut: City-wise distribution
- Gauge: Overall occupancy rate
```

### 3.6 Producers/Hosts Management (45 mins)
**New method:** `show_producers`

**Implementation:**
```python
# Producer List:
- Table: Name, Email, Movies/Events Count, Status
- View button → show their content
- Deactivate/Activate button
- Delete button (cascade delete content or transfer)

# Add Producer:
- Create user account with role='producer'
- Create producer entry
```

---

## Phase 4: Enhancements & Polish (Priority: MEDIUM)
**Estimated Time: 3-4 hours**

### 4.1 Search & Filter Implementation (1 hour)
**Files:** `main.py` (perform_search method, various pages)

**Implementation:**
```python
# Global search (from header):
- Query movies/events WHERE title LIKE ?
- Display results in modal/popup
- Click result → go to detail page

# Genre filter dropdown:
- Extract unique genres from all movies/events
- Multi-select dropdown
- Apply filter → reload grid

# Advanced filters:
- Language, Rating, Duration range
- Combined AND/OR logic
```

### 4.2 Image Handling with Pillow (1 hour)
**New dependency:** Pillow

**Implementation:**
```python
from PIL import Image, ImageTk

def load_movie_image(image_path, size=(200, 300)):
    try:
        img = Image.open(image_path)
        # Maintain aspect ratio
        img.thumbnail(size, Image.Resampling.LANCZOS)
        # Create placeholder border if needed
        return ImageTk.PhotoImage(img)
    except:
        # Return placeholder image
        placeholder = Image.new('RGB', size, color='#333')
        # Add text "No Image"
        return ImageTk.PhotoImage(placeholder)

# Use in movie cards:
tk_image = load_movie_image(f"assets/{movie['cover_image_path']}")
label = tk.Label(card_frame, image=tk_image)
label.image = tk_image  # Keep reference
```

### 4.3 User Feedback Form (30 mins)
**File:** `main.py` (show_feedback_form method)

**Implementation:**
```python
# Feedback Page:
- Large text area for feedback
- Submit button
- On submit:
  - INSERT INTO feedbacks (user_id, text, timestamp, read_flag)
  - Show success message
  - Clear form
```

### 4.4 Testimonials System (30 mins)
**File:** `main.py` (show_user_home method)

**Implementation:**
```python
# Hardcoded testimonials:
testimonials = [
    {"name": "Raj Kumar", "text": "Best booking experience ever!", "rating": 5},
    {"name": "Priya Sharma", "text": "Easy to use and great selection.", "rating": 5},
    # ... 8 more
]

# Display logic:
- Show 3 at a time
- Auto-rotate every 10 seconds
- Simple card UI with name, text, star rating
```

### 4.5 UI Improvements (1 hour)
- Consistent spacing and padding across all pages
- Loading indicators for database operations
- Better error messages with actionable steps
- Confirmation dialogs for destructive actions
- Success notifications (green banner/toast)
- Hover effects on buttons and cards
- Disabled state styling for buttons

---

## Phase 5: Testing & Documentation (Priority: MEDIUM)
**Estimated Time: 2-3 hours**

### 5.1 Testing Checklist (1.5 hours)
```
User Flow:
✓ Registration (user, producer)
✓ Login (all roles)
✓ Browse movies
✓ Search and filter
✓ Movie details
✓ Complete booking flow (with sufficient balance)
✓ Booking failure (insufficient balance)
✓ Add to watchlist
✓ Remove from watchlist
✓ Add wallet balance
✓ Update username (duplicate check)
✓ Update password (validations)
✓ View booking history
✓ Submit feedback

Producer Flow:
✓ View dashboard
✓ Add new movie
✓ Edit existing movie
✓ Delete movie
✓ View analytics (all charts render)
✓ Filter analytics by date/movie

Admin Flow:
✓ Add/edit/delete theatres
✓ Add/edit/delete employees
✓ Add/edit/delete screen schedules
✓ View and mark feedback as read
✓ View analytics
✓ Manage producers

Navigation:
✓ Back button works correctly
✓ Refresh reloads data
✓ Menu toggles properly
✓ Logout clears navigation stack
```

### 5.2 Documentation Updates (1 hour)
- Update README.md with:
  - New features list
  - Dependencies (matplotlib, Pillow)
  - Updated installation steps
  - Screenshots (optional)
- Update PROJECT_STATUS.md:
  - Mark all completed features
  - Known limitations
- Create USER_GUIDE.md:
  - How to book tickets
  - How to manage wallet
  - How to add content (producers)
  - How to manage system (admin)

### 5.3 Code Cleanup (30 mins)
- Remove debug print statements
- Add docstrings to all methods
- Consistent error handling
- Remove unused imports
- Format code consistently

---

## Dependencies to Install

```bash
pip install pillow matplotlib
```

---

## File Structure After Completion

```
pqr-entertainment/
├── main.py                    # ~2000-2500 lines (expanded)
├── database.py                # ~237 lines (no changes needed)
├── populate_demo_data.py      # ~400 lines (updated)
├── tbms.db                    # SQLite database
├── assets/                    # Movie/event cover images
│   ├── Inception.jpg
│   ├── Interstellar.jpg
│   └── ... (16 movies + 2 events)
├── README.md
├── USER_GUIDE.md              # New
└── requirements.txt           # New
```

---

## Estimated Total Time

| Phase | Hours |
|-------|-------|
| Phase 1: Core User Experience | 6-8 |
| Phase 2: Producer Features | 4-5 |
| Phase 3: Admin Features | 5-6 |
| Phase 4: Enhancements & Polish | 3-4 |
| Phase 5: Testing & Documentation | 2-3 |
| **TOTAL** | **20-26 hours** |

---

## Priority Order for Implementation

If time is limited, implement in this order:

1. **Phase 1.2** - Booking flow (MOST CRITICAL - core value)
2. **Phase 1.1** - User homepage (shows all content)
3. **Phase 1.3** - Wallet (needed for bookings)
4. **Phase 1.6** - Booking history (complete user journey)
5. **Phase 1.4** - Watchlist (nice-to-have for users)
6. **Phase 1.5** - Profile updates (lower priority)
7. **Phase 2** - Producer features (demonstrate content management)
8. **Phase 3** - Admin features (demonstrate system management)
9. **Phase 4** - Polish (makes it production-ready)
10. **Phase 5** - Testing (ensures quality)

---

## Next Immediate Step

**START HERE:** Implement Phase 1.1 (User Homepage)
- This will make the application immediately more functional
- Demonstrates the full movie catalog
- Sets up the foundation for the booking flow

Once homepage is done, immediately tackle Phase 1.2 (Booking Flow) as it's the core feature that differentiates this from a simple catalog app.

---

**Last Updated:** 2025-11-09
**Current Progress:** ~35% complete (foundations + data)
**Target:** 100% functional system with all CRUD operations
