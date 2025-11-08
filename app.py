import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-must-change'
# Creates the database file in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Folder where speaker images will be saved
app.config['UPLOAD_FOLDER'] = 'static/images/speakers' 

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
    # Stores the filename of the image (e.g., "prof_dua.jpg")
    image_url = db.Column(db.String(200), default='default.jpg') 

class ImportantDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_str = db.Column(db.String(100), nullable=False) # e.g., "February 15, 2026"

# --- Login Manager Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- Main Public Route ---
@app.route('/')
def home():
    # Fetch all speakers and dates from the database
    speakers = Speaker.query.all()
    dates = ImportantDate.query.all()
    # Pass this data to the template
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
@login_required # This protects the page
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

    filename = 'default.jpg' # Default image if none is uploaded
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        # Ensure the upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

    new_speaker = Speaker(name=name, affiliation=affiliation, bio=bio, image_url=filename)
    db.session.add(new_speaker)
    db.session.commit()
    flash('Speaker added successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/delete_speaker/<int:id>')
@login_required
def delete_speaker(id):
    speaker = Speaker.query.get_or_404(id)
    # You could also add logic here to delete the image file from the server
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

# Add this new route to your app.py
@app.route('/admin/edit_speaker/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_speaker(id):
    speaker = Speaker.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update the speaker's details from the form
        speaker.name = request.form.get('name')
        speaker.affiliation = request.form.get('affiliation')
        speaker.bio = request.form.get('bio')
        
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Save the new image if one is uploaded
            filename = secure_filename(image_file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            speaker.image_url = filename # Update the image filename
            
        db.session.commit()
        flash('Speaker updated successfully!')
        return redirect(url_for('admin'))

    # On GET request, show the edit page with current data
    return render_template('edit_speaker.html', speaker=speaker)

# --- Run the App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates the 'site.db' file if it doesn't exist
    app.run(debug=True)