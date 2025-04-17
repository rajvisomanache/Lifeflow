import os
from app import create_app, db

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app()

with app.app_context():
    try:
        # Attempt to connect and potentially create tables
        db.create_all()
        print("Database tables checked/created (if they didn't exist).")
    except Exception as e:
        print(f"Database connection or table creation failed: {e}")
        print("Ensure your database server is running and credentials in config.py are correct.")
# --- End of Alternative Block ---

if __name__ == '__main__':
    # Set FLASK_APP environment variable if needed, or use --app run:app
    # Example: export FLASK_APP=run.py (Linux/macOS) or set FLASK_APP=run.py (Windows)
    print("Starting Flask development server...")
    print("Access the application via http://127.0.0.1:5000/login-page") # Or your specific login route
    app.run(debug=True) # debug=True reloads on code changes, shows detailed errors