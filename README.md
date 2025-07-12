✅ Step-by-Step Guide (Windows 11)
🔽 1. Download and Extract the ZIP
Click to download: 📦 user_registration_app.zip

Right-click the file → Extract All... → Choose a folder

⚙️ 2. Install Python (if not yet installed)
Download Python from python.org/downloads/windows

During installation, check ✅ "Add Python to PATH"

💻 3. Open Command Prompt in the Project Folder
Open the folder where you extracted the project

Click in the folder address bar and type cmd, then press Enter

You’ll now be in the terminal inside the project folder.

🧪 4. Create a Virtual Environment
bash
Copy

python -m venv venv
▶️ 5. Activate the Virtual Environment
bash
Copy

venv\Scripts\activate
You should see (venv) at the beginning of your command prompt.

📦 6. Install Flask
bash
Copy

pip install flask werkzeug
🚀 7. Run the App
bash
Copy

python app.py
You’ll see something like:

csharp
Copy

 * Running on http://127.0.0.1:5000
🌐 8. Open Your Browser
Go to: http://127.0.0.1:5000

You can now:

Register

View your dashboard

Edit your phone/password

See your saved data

⚠️ Currently, data is not saved permanently (stored in memory). Want me to upgrade it to SQLite?

✅ BONUS: Deploy to GitHub + Render (Free Online Hosting)
If you'd like to put it online, I’ll walk you through:

Pushing to GitHub

Deploying to Render.com

Would you like that now?

Or should I:

Add database storage

Add user login/logout

Add form validation or mobile-friendly design?
