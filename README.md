TravelGo - Full-Stack Travel Booking Platform

TravelGo is a comprehensive, full-stack web application that simulates a real-world travel booking platform. Built with Python (Flask) on the backend and a responsive frontend using Tailwind CSS and vanilla JavaScript, it allows users to search, select, and book various travel services including buses, trains, flights, and hotels.


✨ Key Features

User Authentication: Secure user registration and login system with session management.
Multi-Service Search: Independent search functionalities for:
    🚌 Buses: Search routes and view available services.
    🚆 Trains: Find trains based on origin, destination, and date.
    ✈️ Flights: Search for flights with departure and return date options.
    🏨 Hotels: Find hotels by location.
Interactive Seat Selection: For buses and flights, users can visually select available seats from a dynamic seat map before booking.
Unified Booking System: A single, robust backend endpoint processes and records bookings for all service types (buses, trains, flights, hotels) in a unified 'bookings' table.
User Dashboard: A personalized dashboard where logged-in users can view their complete booking history with all relevant details.
RESTful API Design: The backend exposes clear API endpoints for frontend interactions, such as login, registration, and creating bookings.
Modern Frontend: A clean, responsive UI built with Tailwind CSS that works seamlessly across devices.

🛠️ Tech Stack

Backend: Python, Flask
Database: MySQL
Database Connector: 'PyMySQL'
Frontend: HTML, Tailwind CSS, Vanilla JavaScript (using Fetch API for AJAX)
Templating Engine: Jinja2

🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

Prerequisites

 Python 3.8+
 MySQL Server
 Git

Installation & Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/travelgo.git
    cd travelgo
    ```

2.  Create and activate a virtual environment:
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install the required Python packages:
    ```bash
    pip install Flask pymysql
    ```

4.  Set up the MySQL Database:
    - Connect to your MySQL server.
    - Create a new database named 'travelgo'.
    ```sql
    CREATE DATABASE travelgo;
    ```
    - Run the `database_schema.sql` file (you'll need to create this file) to set up the necessary tables (`users`, `services`, `trains`, `flights`, `hotels`, `bookings`, etc.).

5.  Configure the Application:
    - Open `app.py`.
    - Update the MySQL configuration to match your local setup, especially the password.
    ```python
    # d:\2270\travelgo\app.py

    # --- MySQL Configuration ---
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'YOUR_MYSQL_PASSWORD' # <-- IMPORTANT: Change this!
    app.config['MYSQL_DB'] = 'travelgo'
    ```

6.  Run the Flask Application:
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.


💡 Future Improvements

  Real-time Seat Locking: Implement WebSockets to prevent two users from selecting the same seat simultaneously.
  Payment Gateway Integration: Add a mock or real payment gateway (like Stripe or PayPal) to complete the booking flow.
  Booking Cancellation: Enhance the cancellation feature to free up booked seats/rooms.
  Admin Panel: Create a separate interface for admins to manage users, services, and bookings.
  API Documentation: Use a tool like Swagger/OpenAPI to document the backend API.
