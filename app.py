import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from vercel_blob import put

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key-for-dev')
app.config['UPLOAD_FOLDER'] = 'static/images/speakers' 

# --- Database Configuration ---
db_url = os.environ.get('POSTGRES_URL')
if not db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
else:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Speaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    affiliation = db.Column(db.String(200))
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(300))

class ImportantDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_str = db.Column(db.String(100), nullable=False)

class CommitteeMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False) 
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(200))

class RegistrationFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    ieee_online = db.Column(db.String(50))
    ieee_offline = db.Column(db.String(50))
    non_ieee_online = db.Column(db.String(50))
    non_ieee_offline = db.Column(db.String(50))

class CallForPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_title = db.Column(db.String(100))
    content = db.Column(db.Text)

class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    value = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- Initialization & Auto-Seeding ---
def seed_production_data():
    """Initializes basic data if tables are empty."""
    if not RegistrationFee.query.first():
        fees = [
            RegistrationFee(category="Student (Indian)", ieee_online="₹6,000", ieee_offline="₹8,000", non_ieee_online="₹8,000", non_ieee_offline="₹10,000"),
            RegistrationFee(category="Academician (Indian)", ieee_online="₹11,000", ieee_offline="₹11,000", non_ieee_online="₹13,000", non_ieee_offline="₹13,000")
        ]
        db.session.add_all(fees)
    
    if not ContactInfo.query.first():
        contacts = [
            ContactInfo(label="General Inquiries", value="stesi@jaipur.manipal.edu"),
            ContactInfo(label="Phone Support", value="+91-141-3999100")
        ]
        db.session.add_all(contacts)
    
    if not CallForPaper.query.first():
        db.session.add(CallForPaper(section_title="Paper Formatting", content="IEEE conference format..."))
        
    db.session.commit()

with app.app_context():
    db.create_all()
    # Create admin if not exists
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('12345')))
        db.session.commit()
    seed_production_data()

# --- Main Public Route ---
@app.route('/')
def home():
    return render_template('index.html', 
                           speakers=Speaker.query.all(), 
                           dates=ImportantDate.query.all(),
                           committee=CommitteeMember.query.all(),
                           fees=RegistrationFee.query.all(),
                           cfp=CallForPaper.query.all(),
                           contacts=ContactInfo.query.all())

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- Admin Dashboard ---
@app.route('/admin')
@login_required 
def admin():
    return render_template('admin.html', 
                           speakers=Speaker.query.all(), 
                           dates=ImportantDate.query.all(),
                           committee=CommitteeMember.query.all(),
                           fees=RegistrationFee.query.all(),
                           cfp=CallForPaper.query.all(),
                           contacts=ContactInfo.query.all())

# --- Management Routes (Speakers, Dates, Committee, Fees, etc.) ---

@app.route('/admin/add_speaker', methods=['POST'])
@login_required
def add_speaker():
    image_file = request.files['image']
    image_url = None
    if image_file and image_file.filename != '':
        blob_response = put(secure_filename(image_file.filename), image_file.read())
        image_url = blob_response['url']
    
    new_speaker = Speaker(name=request.form.get('name'), affiliation=request.form.get('affiliation'), 
                          bio=request.form.get('bio'), image_url=image_url)
    db.session.add(new_speaker)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/committee/add', methods=['POST'])
@login_required
def add_committee():
    member = CommitteeMember(category=request.form['category'], name=request.form['name'], position=request.form['position'])
    db.session.add(member)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/committee/delete/<int:id>')
@login_required
def delete_committee(id):
    db.session.delete(CommitteeMember.query.get(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/fees/update/<int:id>', methods=['POST'])
@login_required
def update_fees(id):
    fee = RegistrationFee.query.get(id)
    fee.ieee_online, fee.ieee_offline = request.form['ieee_online'], request.form['ieee_offline']
    fee.non_ieee_online, fee.non_ieee_offline = request.form['non_ieee_online'], request.form['non_ieee_offline']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cfp/update/<int:id>', methods=['POST'])
@login_required
def update_cfp(id):
    item = CallForPaper.query.get(id)
    item.content = request.form['content']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/contact/update/<int:id>', methods=['POST'])
@login_required
def update_contact(id):
    contact = ContactInfo.query.get(id)
    contact.value = request.form['value']
    db.session.commit()
    return redirect(url_for('admin'))

# Date routes (keep existing add_date, edit_date, delete_date)
@app.route('/admin/add_date', methods=['POST'])
@login_required
def add_date():
    db.session.add(ImportantDate(name=request.form.get('name'), date_str=request.form.get('date_str')))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/edit_date/<int:id>', methods=['POST'])
@login_required
def edit_date(id):
    ImportantDate.query.get(id).date_str = request.form.get('date_str')
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_date/<int:id>')
@login_required
def delete_date(id):
    db.session.delete(ImportantDate.query.get(id))
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)