import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from vercel_blob import put

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'trustnet-2026-secure-key')

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

# --- Models ---
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
    sort_order = db.Column(db.Integer, default=0)

class RegistrationFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    ieee_online = db.Column(db.String(50))
    ieee_offline = db.Column(db.String(50))
    non_ieee_online = db.Column(db.String(50))
    non_ieee_offline = db.Column(db.String(50))

class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    value = db.Column(db.Text)

class CFPSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    icon_class = db.Column(db.String(100))
    sort_order = db.Column(db.Integer, default=0)

class CFPPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('cfp_section.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)

class CFPButton(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    icon_class = db.Column(db.String(100))

# --- New Model for Rich Text Sections ---
class ConferenceAbout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100)) # e.g., "Overview"
    content = db.Column(db.Text) # Stores HTML from the editor

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Seeding Logic ---
def seed_production_data():
    if not RegistrationFee.query.first():
        fees = [
            RegistrationFee(category="Student (Indian)", ieee_online="₹6,000", ieee_offline="₹8,000", non_ieee_online="₹8,000", non_ieee_offline="₹10,000"),
            RegistrationFee(category="Academician (Indian)", ieee_online="₹11,000", ieee_offline="₹11,000", non_ieee_online="₹13,000", non_ieee_offline="₹13,000"),
            RegistrationFee(category="Industry (Indian)", ieee_online="₹13,000", ieee_offline="₹13,000", non_ieee_online="₹15,000", non_ieee_offline="₹15,000"),
            RegistrationFee(category="Student (Foreign)", ieee_online="$100", ieee_offline="$120", non_ieee_online="$120", non_ieee_offline="$150"),
            RegistrationFee(category="Academician (Foreign)", ieee_online="$200", ieee_offline="$200", non_ieee_online="$250", non_ieee_offline="$250")
        ]
        db.session.add_all(fees)
    
    if not ContactInfo.query.first():
        contacts = [
            ContactInfo(label="General Inquiries", value="stesi@jaipur.manipal.edu\nRegistration: stesi@jaipur.manipal.edu"),
            ContactInfo(label="Phone Support", value="+91-141-3999100\n+91-141-3999200"),
            ContactInfo(label="Conference Venue", value="Manipal University Jaipur, Rajasthan 303007"),
            ContactInfo(label="Office Hours", value="Monday - Friday: 9:00 AM - 6:00 PM")
        ]
        db.session.add_all(contacts)

    if not CFPSection.query.first():
        s1 = CFPSection(title="Paper Formatting", icon_class="fa-file-lines", sort_order=1)
        s2 = CFPSection(title="Submission Requirements", icon_class="fa-user-secret", sort_order=2)
        s3 = CFPSection(title="Conference Tracks", icon_class="fa-list", sort_order=3)
        db.session.add_all([s1, s2, s3])
        db.session.commit()
        db.session.add(CFPPoint(section_id=s1.id, content="IEEE conference format (two-column layout)"))
        db.session.add(CFPPoint(section_id=s2.id, content="Submit via Microsoft CMT submission system"))
        db.session.add(CFPPoint(section_id=s3.id, content="Smart Grids & Green Energy"))

    if not CFPButton.query.first():
        db.session.add(CFPButton(label="Submit Paper via CMT", url="#", icon_class="fa-arrow-up-right-from-square"))
        db.session.add(CFPButton(label="Download Templates", url="#", icon_class="fa-download"))
    

    if not ConferenceAbout.query.first():
        db.session.add(ConferenceAbout(section_name="Overview", content="<p>The aim of this conference is to present a unified platform...</p>"))
        db.session.add(ConferenceAbout(section_name="Aims and Objectives", content="<p>This Conference aims to bring together leading academic scientists...</p>"))
    
    db.session.commit()

# --- Core Routes ---
@app.route('/')
def home():
    committee = CommitteeMember.query.order_by(CommitteeMember.sort_order).all()
    return render_template('index.html',
        speakers=Speaker.query.all(),
        dates=ImportantDate.query.all(),
        committee=committee,
        fees=RegistrationFee.query.all(),
        contacts=ContactInfo.query.all(),
        cfp_sections=CFPSection.query.order_by(CFPSection.sort_order).all(),
        cfp_points=CFPPoint.query.all(),
        cfp_buttons=CFPButton.query.all(),
        about_content=ConferenceAbout.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid Credentials')
    return render_template('login.html', form=form)

@app.route('/admin')
@login_required
def admin():
    committee = CommitteeMember.query.order_by(CommitteeMember.sort_order).all()
    return render_template('admin.html',
        speakers=Speaker.query.all(),
        dates=ImportantDate.query.all(),
        committee=committee,
        fees=RegistrationFee.query.all(),
        contacts=ContactInfo.query.all(),
        cfp_sections=CFPSection.query.order_by(CFPSection.sort_order).all(),
        cfp_points=CFPPoint.query.all(),
        cfp_buttons=CFPButton.query.all(),
        about_content=ConferenceAbout.query.all())

# --- Fixed Important Dates Management ---

@app.route('/admin/edit_date/<int:id>', methods=['POST'])
@login_required
def edit_date(id):
    date_item = ImportantDate.query.get_or_404(id)
    # We only update the date string as per your HTML form
    date_item.date_str = request.form.get('date_str')
    db.session.commit()
    flash('Date updated successfully!')
    return redirect(url_for('admin'))

# --- Speaker Management ---
@app.route('/admin/add_speaker', methods=['POST'])
@login_required
def add_speaker():
    image_file = request.files.get('image')
    image_url = None
    if image_file and image_file.filename != '':
        ext = os.path.splitext(image_file.filename)[1]
        unique_name = f"speaker-{uuid.uuid4()}{ext}"
        blob_response = put(unique_name, image_file.read())
        image_url = blob_response['url']
    
    db.session.add(Speaker(name=request.form['name'], affiliation=request.form['affiliation'], bio=request.form['bio'], image_url=image_url))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/edit_speaker/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_speaker(id):
    speaker = Speaker.query.get_or_404(id)
    if request.method == 'POST':
        speaker.name, speaker.affiliation, speaker.bio = request.form['name'], request.form['affiliation'], request.form['bio']
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            ext = os.path.splitext(image_file.filename)[1]
            unique_name = f"speaker-{uuid.uuid4()}{ext}"
            blob_response = put(unique_name, image_file.read())
            speaker.image_url = blob_response['url']
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_speaker.html', speaker=speaker)

@app.route('/admin/delete_speaker/<int:id>')
@login_required
def delete_speaker(id):
    db.session.delete(Speaker.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

# --- Committee Management ---
@app.route('/admin/committee/add', methods=['POST'])
@login_required
def add_committee():
    db.session.add(CommitteeMember(category=request.form['category'], name=request.form['name'], position=request.form['position'], sort_order=request.form.get('sort_order', 0)))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/committee/update/<int:id>', methods=['POST'])
@login_required
def update_committee(id):
    m = CommitteeMember.query.get_or_404(id)
    m.category, m.name, m.position = request.form['category'], request.form['name'], request.form['position']
    m.sort_order = request.form.get('sort_order', 0)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/committee/delete/<int:id>')
@login_required
def delete_committee(id):
    db.session.delete(CommitteeMember.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

# --- Data Management ---
@app.route('/admin/add_date', methods=['POST'])
@login_required
def add_date():
    db.session.add(ImportantDate(name=request.form['name'], date_str=request.form['date_str']))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_date/<int:id>')
@login_required
def delete_date(id):
    db.session.delete(ImportantDate.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/fees/update/<int:id>', methods=['POST'])
@login_required
def update_fees(id):
    f = RegistrationFee.query.get_or_404(id)
    f.ieee_online, f.ieee_offline = request.form['ieee_online'], request.form['ieee_offline']
    f.non_ieee_online, f.non_ieee_offline = request.form['non_ieee_online'], request.form['non_ieee_offline']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cfp/point/add', methods=['POST'])
@login_required
def add_cfp_point():
    db.session.add(CFPPoint(section_id=request.form['section_id'], content=request.form['content']))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cfp/point/update/<int:id>', methods=['POST'])
@login_required
def update_cfp_point(id):
    p = CFPPoint.query.get_or_404(id)
    p.content = request.form['content']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cfp/point/delete/<int:id>')
@login_required
def delete_cfp_point(id):
    db.session.delete(CFPPoint.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cfp/button/update/<int:id>', methods=['POST'])
@login_required
def update_cfp_button(id):
    b = CFPButton.query.get_or_404(id)
    b.label, b.url = request.form['label'], request.form['url']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/contact/update/<int:id>', methods=['POST'])
@login_required
def update_contact(id):
    c = ContactInfo.query.get_or_404(id)
    c.value = request.form['value']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/about/update/<int:id>', methods=['POST'])
@login_required
def update_about(id):
    about = ConferenceAbout.query.get_or_404(id)
    about.content = request.form.get('content')
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/reset_all')
def reset_all():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('12345')))
    seed_production_data()
    db.session.commit()
    return "Database fully reset! Visit /admin."

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)