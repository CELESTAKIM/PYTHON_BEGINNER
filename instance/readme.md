# PowerShell commands for setting up and running the GIS Videos Website

# Navigate to the project directory
# Make sure you are in the C:\Users\Administrator\Downloads\new directory
# Then run:
# cd project

# 1. Create a virtual environment
echo "Creating virtual environment..."
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    echo "Error: Failed to create virtual environment. Ensure Python is installed and added to PATH."
    exit 1
}
echo "Virtual environment created."

# 2. Activate the virtual environment
echo "Activating virtual environment..."
.\venv\Scripts\Activate
if ($LASTEXITCODE -ne 0) {
    echo "Error: Failed to activate virtual environment."
    exit 1
}
echo "Virtual environment activated."

# 3. Install required packages
echo "Installing Flask, Flask-SQLAlchemy, and Werkzeug..."
pip install Flask Flask-SQLAlchemy Werkzeug
if ($LASTEXITCODE -ne 0) {
    echo "Error: Failed to install Python packages."
    exit 1
}
echo "Packages installed successfully."

# 4. Create upload directories if they don't exist
echo "Creating upload directories..."
New-Item -ItemType Directory -Force "uploads/profile_pics"
New-Item -ItemType Directory -Force "uploads/videos"
if ($LASTEXITCODE -ne 0) {
    echo "Error: Failed to create upload directories."
    exit 1
}
echo "Upload directories created/ensured."

# 5. (Optional but Recommended for fresh schema) Delete the existing database file
# This ensures a fresh database schema with all columns (e.g., 'twitter') is created.
echo "Checking for and removing existing database.db (if any) to ensure fresh schema..."
if (Test-Path "database.db") {
    Remove-Item "database.db" -Force
    echo "Existing database.db removed."
} else {
    echo "database.db not found. A new one will be created."
}

# 6. Set Flask environment variables
echo "Setting Flask environment variables..."
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development" # Set to 'production' for deployment
echo "FLASK_APP set to app.py"
echo "FLASK_ENV set to development"

# 7. Run the Flask application
echo "Running the Flask application on http://127.0.0.1:5001/"
echo "Press Ctrl+C to stop the server."
flask run --port 5001

# --- Troubleshooting Tips ---
echo "`n--- Troubleshooting Tips ---"
echo "If the application doesn't start or you encounter errors:"

echo "`n1. File Lock/Address in use (sqlalchemy.exc.OperationalError: database is locked or OSError: [WinError 10048] Address already in use):"
echo "   - Another process might be holding a lock on 'database.db' or port 5001 is in use."
echo "   - Try closing other applications that might use databases or port 5001."
echo "   - You can try killing Python processes: taskkill /IM python.exe /F"
echo "   - If port 5001 is in use, try running on a different port (e.g., 5002):"
echo "     flask run --port 5002"
echo "     (Then access at http://127.0.0.1:5002/)"

echo "`n2. Database Schema Verification (e.g., 'no such column: user.twitter'):"
echo "   - This indicates the database schema (structure) is outdated."
echo "   - The script above attempts to fix this by deleting 'database.db' before starting."
echo "   - To manually verify schema: Open a PowerShell/CMD in your project folder, activate venv, then:"
echo "     python -c \"from app import db; from sqlalchemy import inspect; inspector = inspect(db.engine); print(inspector.get_columns('user'))\""
echo "     Ensure 'twitter' and all other expected columns are listed."

echo "`n3. Firewall Settings:"
echo "   - Windows Firewall might be blocking access to port 5001."
echo "   - To allow access (run as Administrator in PowerShell):"
echo "     netsh advfirewall firewall add rule name=\"Flask_App_5001\" dir=in action=allow protocol=TCP localport=5001"

echo "`n4. Flask-Migrate (for schema updates with data preservation):"
echo "   - If you have existing data in 'database.db' and want to update the schema without deleting it, Flask-Migrate is recommended."
echo "   - Install it: pip install Flask-Migrate"
echo "   - You'll need to modify app.py to integrate Flask-Migrate (e.g., `migrate = Migrate(app, db)`)."
echo "   - Basic steps (after modifying app.py and installing):"
echo "     flask db init"
echo "     flask db migrate -m \"Add twitter column to User model\""
echo "     flask db upgrade"
echo "     (Refer to Flask-Migrate documentation for full usage.)"

echo "`n--- Post-Setup Verification ---"
echo "After the server starts, open your web browser and go to: http://127.0.0.1:5001/"
echo "1. Sign up for a new user account at /signin."
echo "2. Log in with the new user account at /login."
echo "3. Log in as an admin with Username: E032-01-1511/2023 and Password: adminpass (or 2024/2025)."
echo "4. Verify user profiles and video uploads work correctly."
echo "5. Check admin dashboard functionalities."