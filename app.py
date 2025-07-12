# app.py
import os
from datetime import datetime, timedelta
import time
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    jsonify # Import jsonify for API responses
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecret' # IMPORTANT: Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folders
UPLOAD_FOLDER_PROFILE_PICS = 'uploads/profile_pics'
UPLOAD_FOLDER_VIDEOS = 'uploads/videos'
ALLOWED_PROFILE_PIC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}
MAX_AUTO_APPROVE_HOURS = 24 # Videos pending for more than 24 hours will be auto-approved

app.config['UPLOAD_FOLDER_PROFILE_PICS'] = UPLOAD_FOLDER_PROFILE_PICS
app.config['UPLOAD_FOLDER_VIDEOS'] = UPLOAD_FOLDER_VIDEOS

db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    county = db.Column(db.String(100), nullable=True)
    school_company = db.Column(db.String(100), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)
    twitter = db.Column(db.String(200), nullable=True) # Explicitly added to resolve error
    bio = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True, default='default_profile.png')

    videos = db.relationship('Video', backref='uploader', lazy=True)
    requests = db.relationship('VideoRequest', backref='requester', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    path = db.Column(db.String(200), unique=True, nullable=False) # Stored filename
    folder_path = db.Column(db.String(200), nullable=True) # User-defined folder/ID
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False) # False for pending, True for approved

    access_requests = db.relationship('VideoRequest', backref='requested_video', lazy=True)

    def __repr__(self):
        return f'<Video {self.title}>'

class VideoRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending') # pending, approved, denied

    def __repr__(self):
        return f'<VideoRequest {self.id} User:{self.user_id} Video:{self.video_id} Status:{self.status}>'

# --- Helper Functions ---
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Hardcoded admin IDs for demonstration. In production, use a database role system.
        admin_ids = [
            'E032-01-1511/2023',
            'E032-01-1511/2024',
            'E032-01-1511/2025'
        ]
        if 'admin_user_id' not in session or session['admin_user_id'] not in admin_ids:
            flash('Admin access required.', 'danger')
            return redirect(url_for('login')) # Or a dedicated unauthorized page
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session or 'admin_user_id' in session:
        return redirect(url_for('video_list'))
    return redirect(url_for('login'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signin.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('signin.html')

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered. Please use a different one or login.', 'danger')
            return render_template('signin.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {e}', 'danger')
            app.logger.error(f"Error during signin: {e}")
            return render_template('signin.html')
    return render_template('signin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check for admin login first
        admin_ids = [
            'E032-01-1511/2023',
            'E032-01-1511/2024',
            'E032-01-1511/2025'
        ]
        if username in admin_ids and password == 'adminpass': # Simple admin password for this example
            session.clear() # Clear any existing user session
            session['admin_user_id'] = username
            flash(f'Welcome, Admin {username}!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Then check for regular user login
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.clear() # Clear any existing admin session
            session['user_id'] = user.id
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('video_list'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@app.route('/signout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            user.county = request.form['county']
            user.school_company = request.form['school_company']
            user.linkedin = request.form['linkedin']
            user.github = request.form['github']
            user.twitter = request.form['twitter']
            user.bio = request.form['bio']
            user.experience = request.form['experience']
            user.skills = request.form['skills']

            # Handle profile picture upload
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and allowed_file(file.filename, ALLOWED_PROFILE_PIC_EXTENSIONS):
                    filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
                    filepath = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PICS'], filename)
                    file.save(filepath)
                    user.profile_pic = filename
                elif file and file.filename != '':
                    flash('Invalid profile picture format. Allowed: PNG, JPG, JPEG, GIF.', 'warning')

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')
            app.logger.error(f"Error updating profile for user {user_id}: {e}")
    return render_template('profile.html', user=user)

@app.route('/uploads/profile_pics/<filename>')
def uploaded_profile_pic(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_PROFILE_PICS'], filename)

@app.route('/uploads/videos/<filename>')
def uploaded_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_VIDEOS'], filename)

@app.route('/video_upload', methods=['GET', 'POST'])
@login_required
def video_upload():
    if request.method == 'POST':
        title = request.form['title']
        folder_path = request.form.get('folder_path', '')
        user_id = session['user_id']

        if 'video_file' not in request.files:
            flash('No video file part.', 'danger')
            return render_template('video_upload.html')

        file = request.files['video_file']
        if file.filename == '':
            flash('No selected video file.', 'danger')
            return render_template('video_upload.html')

        if not title:
            flash('Video title is required.', 'danger')
            return render_template('video_upload.html')

        if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
            filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], filename)
            try:
                file.save(filepath)
                # Video is initially not approved
                new_video = Video(user_id=user_id, title=title, path=filename, folder_path=folder_path, approved=False)
                db.session.add(new_video)
                db.session.commit()
                flash('Video uploaded successfully! It is pending admin approval.', 'success')
                return redirect(url_for('video_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error uploading video: {e}', 'danger')
                app.logger.error(f"Error saving video file or database entry: {e}")
                return render_template('video_upload.html')
        else:
            flash('Invalid video file format. Allowed: MP4, AVI, MOV.', 'danger')
    return render_template('video_upload.html')

@app.route('/video_list')
@login_required
def video_list():
    user_id = session['user_id']
    # Auto-approve videos older than MAX_AUTO_APPROVE_HOURS that are still pending
    # This check will happen on every request to video_list, which is fine for small apps.
    # For very large apps, consider a background task.
    with app.app_context(): # Ensure this runs within an app context
        pending_videos_for_auto_approval = Video.query.filter_by(approved=False).all()
        for video in pending_videos_for_auto_approval:
            if datetime.utcnow() - video.upload_time > timedelta(hours=MAX_AUTO_APPROVE_HOURS):
                video.approved = True
                try:
                    db.session.commit()
                    # print(f"Auto-approved video: {video.title}") # For debugging
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error during auto-approval of video {video.id}: {e}")

    videos = Video.query.filter_by(approved=True).order_by(Video.upload_time.desc()).all()
    # Check if the current user has requested access to any of the listed videos
    requested_video_ids = {
        req.video_id
        for req in VideoRequest.query.filter_by(user_id=user_id).all()
    }
    return render_template('video_list.html', videos=videos, requested_video_ids=requested_video_ids)

@app.route('/request_video/<int:video_id>')
@login_required
def request_video(video_id):
    user_id = session['user_id']
    video = Video.query.get_or_404(video_id)

    # Prevent requesting access to own videos or already approved videos
    if video.user_id == user_id:
        flash("You own this video, no request needed.", "info")
        return redirect(url_for('video_list'))
    
    # If the video is already broadly approved, no individual request is needed
    if video.approved: 
        flash("This video is already approved for viewing.", "info")
        return redirect(url_for('video_list'))

    existing_request = VideoRequest.query.filter_by(user_id=user_id, video_id=video_id).first()
    if existing_request:
        flash(f'You have already {existing_request.status} access for this video.', 'info')
    else:
        new_request = VideoRequest(user_id=user_id, video_id=video_id, status='pending')
        try:
            db.session.add(new_request)
            db.session.commit()
            flash('Video access request submitted! Waiting for admin approval.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting request: {e}', 'danger')
            app.logger.error(f"Error submitting video request for user {user_id} and video {video_id}: {e}")
    return redirect(url_for('video_list'))

@app.route('/view_video/<int:video_id>')
@login_required
def view_video(video_id):
    user_id = session['user_id']
    video = Video.query.get_or_404(video_id)

    # Check if the video is approved or if the user is the uploader or has an approved request
    has_access = False
    if video.approved or video.user_id == user_id:
        has_access = True
    else:
        approved_request = VideoRequest.query.filter_by(user_id=user_id, video_id=video_id, status='approved').first()
        if approved_request:
            has_access = True

    if not has_access:
        flash('You do not have permission to view this video. Please request access.', 'danger')
        return redirect(url_for('video_list'))

    return render_template('video_viewer.html', video=video)

# --- Admin Dashboard ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    videos = Video.query.order_by(Video.upload_time.desc()).all()
    pending_requests = VideoRequest.query.filter_by(status='pending').all()
    approved_requests = VideoRequest.query.filter_by(status='approved').all()
    denied_requests = VideoRequest.query.filter_by(status='denied').all()
    return render_template(
        'admin_dashboard.html',
        users=users,
        videos=videos,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        denied_requests=denied_requests
    )

@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            user.county = request.form['county']
            user.school_company = request.form['school_company']
            user.linkedin = request.form['linkedin']
            user.github = request.form['github']
            user.twitter = request.form['twitter']
            user.bio = request.form['bio']
            user.experience = request.form['experience']
            user.skills = request.form['skills']

            # Admin can also reset password (optional, for demo purposes)
            new_password = request.form.get('new_password')
            if new_password:
                user.password = generate_password_hash(new_password)

            # Handle profile picture upload by admin
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and allowed_file(file.filename, ALLOWED_PROFILE_PIC_EXTENSIONS):
                    filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
                    filepath = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PICS'], filename)
                    file.save(filepath)
                    user.profile_pic = filename
                elif file and file.filename != '':
                    flash('Invalid profile picture format. Allowed: PNG, JPG, JPEG, GIF.', 'warning')

            db.session.commit()
            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {e}', 'danger')
            app.logger.error(f"Admin error updating user {user_id}: {e}")
    return render_template('edit_user.html', user=user)

@app.route('/admin/review_request/<int:request_id>/<action>')
@admin_required
def admin_review_request(request_id, action):
    req = VideoRequest.query.get_or_404(request_id)
    # video_to_approve = Video.query.get(req.video_id) # Not directly used in simple action

    try:
        if action == 'approve':
            req.status = 'approved'
            flash(f'Request from {req.requester.username} for "{req.requested_video.title}" approved.', 'success')
        elif action == 'deny':
            req.status = 'denied'
            flash(f'Request from {req.requester.username} for "{req.requested_video.title}" denied.', 'info')
        elif action == 'delete': # Allow admin to remove requests completely
            db.session.delete(req)
            flash(f'Request from {req.requester.username} for "{req.requested_video.title}" deleted.', 'info')
        else:
            flash('Invalid action.', 'danger')
            return redirect(url_for('admin_dashboard'))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing request: {e}', 'danger')
        app.logger.error(f"Error processing video request {request_id}: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_video_approval/<int:video_id>')
@admin_required
def admin_toggle_video_approval(video_id):
    video = Video.query.get_or_404(video_id)
    video.approved = not video.approved
    try:
        db.session.commit()
        flash(f'Video "{video.title}" approval status toggled to {video.approved}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling video approval: {e}', 'danger')
        app.logger.error(f"Error toggling video approval for video {video_id}: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/bulk_review_requests', methods=['POST'])
@admin_required
def admin_bulk_review_requests():
    """
    Handles bulk approval, denial, or deletion of video access requests.
    Expects a JSON payload with 'request_ids' (list of IDs) and 'action' (string).
    Handles 'approve_all' and 'deny_all' actions for pending requests.
    """
    if request.method == 'POST':
        try:
            data = request.get_json()
            request_ids = data.get('request_ids', [])
            action = data.get('action')

            if not action:
                return jsonify({'success': False, 'message': 'Action not specified.'}), 400

            # Define valid actions
            valid_actions = ['approve', 'deny', 'delete', 'approve_all', 'deny_all']
            if action not in valid_actions:
                return jsonify({'success': False, 'message': 'Invalid action specified.'}), 400

            requests_to_process = []
            if action == 'approve_all':
                requests_to_process = VideoRequest.query.filter_by(status='pending').all()
            elif action == 'deny_all':
                requests_to_process = VideoRequest.query.filter_by(status='pending').all()
            else: # Specific selected requests (approve, deny, delete)
                if not request_ids:
                    return jsonify({'success': False, 'message': 'No request IDs provided for selected action.'}), 400
                requests_to_process = VideoRequest.query.filter(VideoRequest.id.in_(request_ids)).all()
                # Filter out requests that don't match the action's typical status if needed
                # (e.g., trying to approve an already approved request might not make sense)

            processed_count = 0
            for req in requests_to_process:
                if action == 'approve' or action == 'approve_all':
                    if req.status != 'approved': # Only change if not already approved
                        req.status = 'approved'
                        processed_count += 1
                elif action == 'deny' or action == 'deny_all':
                    if req.status != 'denied': # Only change if not already denied
                        req.status = 'denied'
                        processed_count += 1
                elif action == 'delete':
                    db.session.delete(req)
                    processed_count += 1
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Bulk action "{action}" completed for {processed_count} requests.'})

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during bulk review: {e}")
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
    return jsonify({'success': False, 'message': 'Method not allowed.'}), 405


@app.route('/remove_admin_credentials')
@admin_required
def remove_admin_credentials():
    # In a real application, this would be a more robust credential management system.
    # For this demo, it just logs out the current admin session.
    session.pop('admin_user_id', None)
    flash('Admin credentials removed (session cleared).', 'info')
    return redirect(url_for('login'))

@app.route('/terms_conditions')
def terms_conditions():
    return render_template('terms_conditions.html')

# --- Context Processors (for navbar profile pic) ---
@app.context_processor
def inject_user_profile_pic():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return {'current_user_profile_pic': user.profile_pic}
    return {'current_user_profile_pic': None}

# --- Initialize Database and Upload Folders ---
# This block ensures tables are created and directories exist when app.py is executed directly.
# For 'flask run', Flask handles the app context automatically.
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            os.makedirs(app.config['UPLOAD_FOLDER_PROFILE_PICS'], exist_ok=True)
            os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)
            print("Database tables and upload directories ensured.")
        except Exception as e:
            print(f"Error ensuring database/directories: {e}")

    app.run(host='0.0.0.0', port=5001, debug=True)