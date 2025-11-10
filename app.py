import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from vercel_blob import put # For Vercel Blob uploads

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-must-change'
# Folder where speaker images will be *temporarily* held during upload
app.config['UPLOAD_FOLDER'] = 'static/images/speakers' 

# --- Database Configuration ---
# Get the database URL from Vercel's environment variables
db_url = os.environ.get('POSTGRES_URL')

if not db_url:
    # If VERCEL_URL is missing, fall back to a local SQLite file for testing
    print("WARNING: POSTGRES_URL not found. Using local sqlite db 'site.db'")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
else:
    # Vercel gives 'postgres://' but SQLAlchemy needs 'postgresql://'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirects to /login if user is not logged in

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Speaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    affiliation = db.Column(db.String(200))
    bio = db.Column(db.Text)
    # Stores the full public URL from Vercel Blob
    image_url = db.Column(db.String(300), default=None) 

class ImportantDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_str = db.Column(db.String(100), nullable=False)

# --- Login Manager Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- Create Database Tables and Default Admin ---
def create_default_admin():
    """Checks if admin user exists, if not, creates one."""
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found, creating one...")
            # Change '12345' to your desired default password
            hashed_password = generate_password_hash('12345') 
            new_admin = User(username='admin', password_hash=hashed_password)
            db.session.add(new_admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.session.rollback() # Rollback in case of error

# Create tables and admin user
with app.app_context():
    db.create_all()
    create_default_admin()

# --- Main Public Route ---
@app.route('/')
def home():
    speakers = Speaker.query.all()
    dates = ImportantDate.query.all()
    return render_template('index.html', speakers=speakers, dates=dates)

# --- Admin Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('admin'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- Admin Dashboard Routes ---
@app.route('/admin')
@login_required 
def admin():
    speakers = Speaker.query.all()
    dates = ImportantDate.query.all()
    return render_template('admin.html', speakers=speakers, dates=dates)

# --- Speaker Management Routes ---
@app.route('/admin/add_speaker', methods=['POST'])
@login_required
def add_speaker():
    name = request.form.get('name')
    affiliation = request.form.get('affiliation')
    bio = request.form.get('bio')
    image_file = request.files['image']

    image_url = None # Default image
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        # Upload to Vercel Blob
        blob_response = put(filename, image_file.read(), add_random_suffix=True)
        image_url = blob_response['url'] # Get the public URL

    new_speaker = Speaker(name=name, affiliation=affiliation, bio=bio, image_url=image_url)
    db.session.add(new_speaker)
    db.session.commit()
    flash('Speaker added successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/edit_speaker/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_speaker(id):
    speaker = Speaker.query.get_or_404(id)
    if request.method == 'POST':
        speaker.name = request.form.get('name')
        speaker.affiliation = request.form.get('affiliation')
        speaker.bio = request.form.get('bio')
        
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Upload new image to Vercel Blob
            filename = secure_filename(image_file.filename)
            blob_response = put(filename, image_file.read(), add_random_suffix=True)
            speaker.image_url = blob_response['url'] # Update the image URL
            
        db.session.commit()
        flash('Speaker updated successfully!')
        return redirect(url_for('admin'))
    return render_template('edit_speaker.html', speaker=speaker)

@app.route('/admin/delete_speaker/<int:id>')
@login_required
def delete_speaker(id):
    speaker = Speaker.query.get_or_404(id)
    # Note: This does not delete the image from Vercel Blob, only the db record
    db.session.delete(speaker)
    db.session.commit()
    flash('Speaker deleted.')
    return redirect(url_for('admin'))

# --- Date Management Routes ---
@app.route('/admin/add_date', methods=['POST'])
@login_required
def add_date():
    name = request.form.get('name')
    date_str = request.form.get('date_str')
    if name and date_str:
        new_date = ImportantDate(name=name, date_str=date_str)
        db.session.add(new_date)
        db.session.commit()
        flash('Date added successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/edit_date/<int:id>', methods=['POST'])
@login_required
def edit_date(id):
    date = ImportantDate.query.get_or_404(id)
    date.date_str = request.form.get('date_str')
    db.session.commit()
    flash('Date updated.')
    return redirect(url_for('admin'))

@app.route('/admin/delete_date/<int:id>')
@login_required
def delete_date(id):
    date = ImportantDate.query.get_or_404(id)
    db.session.delete(date)
    db.session.commit()
    flash('Date deleted.')
    return redirect(url_for('admin'))

# --- Run the App (for local development) ---
if __name__ == '__main__':
    app.run(debug=True)