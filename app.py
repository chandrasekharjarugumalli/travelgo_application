from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
import pymysql.cursors
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

# Initialize the Flask application
app = Flask(__name__)
# A strong secret key is required for session management
app.secret_key = os.urandom(24)

# --- MySQL Configuration ---
# Update these details to match your MySQL server configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'P@ssword19' # IMPORTANT: Replace with your actual MySQL password
app.config['MYSQL_DB'] = 'travelgo'

def get_db_connection():
    """Creates and returns a new database connection."""
    connection = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# --- Main & Static Routes ---

@app.route('/')
def home():
    """Renders the homepage."""
    return render_template('home.html')

@app.route('/about')
def about():
    """Renders the About Us page."""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Renders the Contact Us page."""
    return render_template('contactus.html')


# --- Authentication Routes ---

@app.route('/login_page')
def login_page():
    """Serves the login page."""
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    """Serves the registration page."""
    return render_template('registration.html')
    
@app.route('/register', methods=['POST'])
def register():
    """API endpoint to handle new user registration."""
    data = request.get_json()
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409
            
            # Insert new user into the database
            hashed_password = generate_password_hash(password)
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        conn.commit()
        return jsonify({'success': True, 'message': 'Account created successfully! Please log in.'})
    except pymysql.MySQLError as e:
        # Log the error for debugging
        print(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'A database error occurred.'}), 500
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """API endpoint to handle user login."""
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    
    try:
        conn = get_db_connection()
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
        return jsonify({'success': False, 'message': 'Database connection error.'}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
    except pymysql.MySQLError as e:
        print(f"Database query error: {e}")
        return jsonify({'success': False, 'message': 'Database query error.'}), 500
    finally:
        conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'Email not found.'}), 401

    if not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Incorrect password.'}), 401

    session['user_email'] = user['email']
    session['user_name'] = user['name']
    session['user_id'] = user['id']
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    """Clears the user session and redirects to homepage."""
    session.clear()
    return redirect(url_for('home')) 

@app.route('/check_session')
def check_session():
    """API endpoint for the frontend to check if a user is logged in."""
    if 'user_email' in session:
        return jsonify({'logged_in': True, 'user': {'name': session.get('user_name')}})
    return jsonify({'logged_in': False})

# --- Feature & Booking Flow Routes ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
 
    user_id = session['user_id']
    bookings = []
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Fetch all bookings for the user from a single table
            cur.execute(""" 
                SELECT id, service_type, details, total_price, booking_date 
                FROM bookings 
                WHERE user_id = %s 
                ORDER BY booking_date DESC
            """, (user_id,))
            bookings_raw = cur.fetchall()
            for booking in bookings_raw:
                booking['details'] = json.loads(booking['details'])
                bookings.append(booking)
    except pymysql.MySQLError as e:
        print(f"Database error in dashboard: {e}")
        # Render the page with empty lists in case of an unexpected DB error
        return render_template('userdashboard.html', bookings=[])
    finally:
        conn.close()

    return render_template('userdashboard.html', bookings=bookings)

# --- Search Pages ---
@app.route('/bus_search', methods=['GET', 'POST'])
def bus_search():
    """Displays the bus search page and handles search."""
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    
    today_date = date.today().isoformat()

    services = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if request.method == 'POST':
                # On POST request (clicking search), show all buses irrespective of date
                query = "SELECT * FROM services"
                cur.execute(query)
                services = cur.fetchall()
            else:
                # On GET request, show all buses for today
                cur.execute("SELECT * FROM services WHERE travel_date = %s", (today_date,))
                services = cur.fetchall()
    except pymysql.MySQLError as e:
        print(f"Database error in bus_search: {e}")
    finally:
        conn.close()

    return render_template('bussearch.html', services=services, today_date=today_date)


@app.route('/search_hotels', methods=['GET'])
def search_hotels():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    location = request.args.get('location')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if location:
                # Use a LIKE query to allow for partial matches
                cursor.execute("SELECT * FROM hotels WHERE location LIKE %s", (f"%{location}%",))
            else:
                # If no location is specified, show all hotels
                cursor.execute("SELECT * FROM hotels")
            hotels = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Database error in search_hotels: {e}")
        hotels = []
    finally:
        conn.close()

    return render_template('hotelsearch.html', hotels=hotels)


@app.route('/book_hotel/<int:hotel_id>', methods=['GET'])
def book_hotel(hotel_id):
    """Displays the booking confirmation page for a specific hotel."""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    # Use today's date as a default check-in date
    checkin_date = date.today().isoformat()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hotels WHERE id = %s", (hotel_id,))
            hotel = cur.fetchone()
    finally:
        conn.close()

    if not hotel:
        return "Hotel not found", 404

    return render_template('hotel_booking.html', hotel=hotel, checkin_date=checkin_date)


@app.route('/select_seats/<int:service_id>')
def select_seats(service_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    travel_date = request.args.get('travel_date')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get service details
            cur.execute("SELECT * FROM services WHERE id = %s", (service_id,))
            service = cur.fetchone()

            # Get seat availability
            cur.execute("SELECT seat_number, is_booked FROM bus_seats WHERE service_id = %s ORDER BY id", (service_id,))
            seats = cur.fetchall()
    finally:
        conn.close()

    if not service:
        return "Service not found", 404

    return render_template('seat_selection.html', service=service, seats=seats, travel_date=travel_date)

@app.route('/train_search', methods=['GET', 'POST'])
def train_search():
    """Displays the train search page and handles search."""
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    
    trains = []
    if request.method == 'POST':
        from_city = request.form.get('from_city')
        to_city = request.form.get('to_city')
        travel_date = request.form.get('travel_date')
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Build query with optional filters
                query = "SELECT * FROM trains WHERE 1=1"
                params = []
                if from_city:
                    query += " AND origin LIKE %s"
                    params.append(f"%{from_city}%")
                if to_city:
                    query += " AND destination LIKE %s"
                    params.append(f"%{to_city}%")
                if travel_date:
                    query += " AND travel_date = %s"
                    params.append(travel_date)
                
                cur.execute(query, params)
                trains = cur.fetchall()
        except pymysql.MySQLError as e:
            print(f"Database error in train_search: {e}")
            # In case of error, trains remains an empty list
        finally:
            conn.close()

    return render_template('train_search.html', trains=trains)

@app.route('/book_train/<int:train_id>')
def book_train(train_id):
    """Displays the class and quantity selection page for a specific train."""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    travel_date = request.args.get('travel_date') # Correctly get the date parameter

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trains WHERE id = %s", (train_id,))
            train = cur.fetchone()
    finally:
        conn.close()

    if not train:
        return "Train not found", 404

    return render_template('train_booking.html', train=train, travel_date=travel_date)

@app.route('/flight_search', methods=['GET', 'POST'])
def flight_search():
    """Displays the flight search page and handles search."""
    if 'user_email' not in session:
        return redirect(url_for('login_page'))

    flights = []
    if request.method == 'POST':
        from_airport = request.form.get('from_airport')
        to_airport = request.form.get('to_airport')
        departure_date = request.form.get('departure_date')

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT * FROM flights WHERE 1=1"
                params = []
                if from_airport:
                    query += " AND origin LIKE %s"
                    params.append(f"%{from_airport}%")
                if to_airport:
                    query += " AND destination LIKE %s"
                    params.append(f"%{to_airport}%")
                # Assuming you add a 'departure_date' column of type DATE to your 'flights' table
                if departure_date:
                    query += " AND departure_date = %s"
                    params.append(departure_date)

                cur.execute(query, params)
                flights = cur.fetchall()
        except pymysql.MySQLError as e:
            print(f"Database error in flight_search: {e}")
        finally:
            conn.close()

    return render_template('flight_search.html', flights=flights)

@app.route('/select_flight_seats/<int:flight_id>')
def select_flight_seats(flight_id):
    """Displays the seat selection map for a specific flight."""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    travel_date = request.args.get('departure_date')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get flight details
            cur.execute("SELECT * FROM flights WHERE id = %s", (flight_id,))
            flight = cur.fetchone()

            # Get seat availability for the flight
            cur.execute("SELECT seat_number, is_booked FROM flight_seats WHERE flight_id = %s ORDER BY id", (flight_id,))
            seats = cur.fetchall()
    finally:
        conn.close()

    if not flight:
        return "Flight not found", 404

    return render_template('flight_seat_selection.html', flight=flight, seats=seats, travel_date=travel_date)


# --- Booking Process ---
@app.route('/create_booking', methods=['POST'])
def create_booking():
    """
    A unified API endpoint to create bookings for any service type.
    Handles bus seat reservations and saves booking details for all types.
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    data = request.get_json()
    service_type = data.get('type')
    service_id = data.get('service_id')
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # --- Start Transaction ---
            conn.begin()

            details = {}
            total_price = 0
            travel_date = data.get('date') if data.get('date') else None

            if service_type == 'bus':
                selected_seats = data.get('seats', '').split(',')
                if not selected_seats or not service_id:
                    raise ValueError("Missing bus service ID or seats")

                # Lock seats and create booking
                cur.execute("SELECT name, from_city, to_city, price FROM services WHERE id = %s", (service_id,))
                service_info = cur.fetchone()
                total_price = len(selected_seats) * service_info['price']

                details = {
                    "name": service_info['name'],
                    "from": service_info['from_city'],
                    "to": service_info['to_city'],
                    "seats": ", ".join(selected_seats),
                    "date": travel_date or 'N/A'
                }

                # Mark seats as booked
                placeholders = ','.join(['%s'] * len(selected_seats))
                sql = f"UPDATE bus_seats SET is_booked = 1, user_id = %s WHERE service_id = %s AND seat_number IN ({placeholders})"
                params = [user_id, service_id] + selected_seats
                cur.execute(sql, params)

            elif service_type == 'train':
                quantity = int(data.get('quantity', 1))
                travel_class = data.get('class', 'Sleeper')

                # Fetch service details to store in the booking
                cur.execute("SELECT * FROM trains WHERE id = %s", (service_id,))
                service_info = cur.fetchone()
                if not service_info:
                    raise ValueError(f"{service_type} not found.")
                
                # Calculate price based on class multiplier
                price_multiplier = {'Sleeper': 1.0, 'AC Chair': 1.5, 'First Class': 2.5}.get(travel_class, 1.0)
                total_price = float(service_info['price']) * price_multiplier * quantity

                details = {
                    "name": service_info.get('name'),
                    "details": f"{quantity} ticket(s) in {travel_class}",
                    "from": service_info['origin'],
                    "to": service_info['destination'],
                    "date": travel_date or 'N/A'
                }
            
            elif service_type == 'flight':
                selected_seats = data.get('seats', '').split(',')
                if not selected_seats or not service_id:
                    raise ValueError("Missing flight service ID or seats")

                cur.execute("SELECT airline, number, origin, destination, price FROM flights WHERE id = %s", (service_id,))
                service_info = cur.fetchone()
                total_price = len(selected_seats) * float(service_info['price'])

                details = {
                    "name": f"{service_info['airline']} {service_info['number']}",
                    "from": service_info['origin'],
                    "to": service_info['destination'],
                    "seats": ", ".join(selected_seats),
                    "date": travel_date or 'N/A'
                }

                # Mark seats as booked for the flight
                placeholders = ','.join(['%s'] * len(selected_seats))
                sql = f"UPDATE flight_seats SET is_booked = 1, user_id = %s WHERE flight_id = %s AND seat_number IN ({placeholders})"
                params = [user_id, service_id] + selected_seats
                cur.execute(sql, params)
            
            elif service_type == 'hotel':
                # Fetch hotel details for the booking record
                cur.execute("SELECT * FROM hotels WHERE id = %s", (service_id,))
                service_info = cur.fetchone()
                if not service_info:
                    raise ValueError("Hotel not found.")
                
                total_price = service_info['price_per_night']
                details = {
                    "name": service_info['name'],
                    "from": service_info['location'], # Using 'from' for location consistency
                    "to": "N/A",
                    "details": "1 Night Stay",
                    "date": travel_date or 'N/A'
                }

            
            # Insert into the unified bookings table
            cur.execute(
                "INSERT INTO bookings (user_id, service_type, service_id, details, total_price) VALUES (%s, %s, %s, %s, %s)",
                (user_id, service_type, service_id, json.dumps(details), total_price)
            )
            booking_id = cur.lastrowid
            
            # --- Commit Transaction ---
            conn.commit()
            return jsonify({'status': 'success', 'booking_id': booking_id})

    except (pymysql.MySQLError, ValueError) as e:
        conn.rollback()
        print(f"Error during booking creation: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to create booking: {e}'}), 500
    finally:
        conn.close()

# --- Placeholder Routes (for pages without backend logic yet) ---
@app.route('/order')
def order(): return render_template('order.html')

@app.route('/quiz')
def quiz(): return render_template('quiz.html')

@app.route('/virtual_exhibition')
def virtual_exhibition(): return render_template('virtual_exhibition.html')

@app.route('/wishlist')
def wishlist(): return render_template('wishlist.html')

# --- API Routes for Client-Side Actions ---

@app.route('/api/cancel_booking', methods=['POST'])
def cancel_booking():
    """API endpoint to cancel a booking from the dashboard."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 401
        
    data = request.get_json()
    booking_id = data.get('booking_id')
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Ensure the booking belongs to the logged-in user before deleting for security
            deleted_rows_count = cur.execute("DELETE FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        conn.commit()
    finally:
        conn.close()
    
    if deleted_rows_count > 0:
        return jsonify({'success': True, 'message': 'Booking cancelled successfully.'})
        
    return jsonify({'success': False, 'message': 'Cancellation failed. Booking not found or permission denied.'}), 400

# --- Main entry point for the application ---
if __name__ == '__main__':
    app.run(debug=True)
