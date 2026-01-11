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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'trustnet-secret-key-2026')

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

# --- Call for Paper Models ---
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Seeding Logic ---
def seed_production_data():
    with app.app_context():
        # 1. Registration Fees
        if not RegistrationFee.query.first():
            fees = [
                RegistrationFee(category="Student (Indian)", ieee_online="₹6,000", ieee_offline="₹8,000", non_ieee_online="₹8,000", non_ieee_offline="₹10,000"),
                RegistrationFee(category="Academician (Indian)", ieee_online="₹11,000", ieee_offline="₹11,000", non_ieee_online="₹13,000", non_ieee_offline="₹13,000"),
                RegistrationFee(category="Industry (Indian)", ieee_online="₹13,000", ieee_offline="₹13,000", non_ieee_online="₹15,000", non_ieee_offline="₹15,000"),
                RegistrationFee(category="Student (Foreign)", ieee_online="$100", ieee_offline="$120", non_ieee_online="$120", non_ieee_offline="$150"),
                RegistrationFee(category="Academician (Foreign)", ieee_online="$200", ieee_offline="$200", non_ieee_online="$250", non_ieee_offline="$250")
            ]
            db.session.add_all(fees)
        
        # 2. Contacts
        if not ContactInfo.query.first():
            contacts = [
                ContactInfo(label="General Inquiries", value="stesi@jaipur.manipal.edu\nRegistration: stesi@jaipur.manipal.edu"),
                ContactInfo(label="Phone Support", value="+91-141-3999100\n+91-141-3999200"),
                ContactInfo(label="Conference Venue", value="Manipal University Jaipur, Rajasthan 303007"),
                ContactInfo(label="Office Hours", value="Monday - Friday: 9:00 AM - 6:00 PM")
            ]
            db.session.add_all(contacts)

        # 3. CFP Sections & Points
        if not CFPSection.query.first():
            s1 = CFPSection(title="Paper Formatting", icon_class="fa-file-lines", sort_order=1)
            s2 = CFPSection(title="Submission Requirements", icon_class="fa-user-secret", sort_order=2)
            db.session.add_all([s1, s2])
            db.session.commit()
            
            p1 = CFPPoint(section_id=s1.id, content="IEEE conference format (two-column layout)")
            p2 = CFPPoint(section_id=s2.id, content="Submit via Microsoft CMT submission system")
            db.session.add_all([p1, p2])

        # 4. CFP Buttons
        if not CFPButton.query.first():
            db.session.add(CFPButton(label="Submit Paper via CMT", url="#", icon_class="fa-arrow-up-right-from-square"))
        
        db.session.commit()

# --- Database Reset & Re-Seed ---
@app.route('/reset_all')
def reset_all():
    db.drop_all()
    db.create_all()
    # Create Admin
    admin_user = User(username='admin', password_hash=generate_password_hash('12345'))
    db.session.add(admin_user)
    db.session.commit()
    seed_production_data()
    return "Database reset and seeded with structured CFP and Foreign Fees!"

# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html',
        speakers=Speaker.query.all(),
        dates=ImportantDate.query.all(),
        committee=CommitteeMember.query.order_by(CommitteeMember.sort_order).all(),
        fees=RegistrationFee.query.all(),
        contacts=ContactInfo.query.all(),
        cfp_sections=CFPSection.query.order_by(CFPSection.sort_order).all(),
        cfp_points=CFPPoint.query.all(),
        cfp_buttons=CFPButton.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid Credentials')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html',
        speakers=Speaker.query.all(),
        dates=ImportantDate.query.all(),
        committee=CommitteeMember.query.order_by(CommitteeMember.sort_order).all(),
        fees=RegistrationFee.query.all(),
        contacts=ContactInfo.query.all(),
        cfp_sections=CFPSection.query.order_by(CFPSection.sort_order).all(),
        cfp_points=CFPPoint.query.all(),
        cfp_buttons=CFPButton.query.all())

# --- CRUD Routes (Committee, Fees, CFP, Contacts) ---
@app.route('/admin/committee/add', methods=['POST'])
@login_required
def add_committee():
    db.session.add(CommitteeMember(category=request.form['category'], name=request.form['name'], position=request.form['position'], sort_order=request.form.get('sort_order', 0)))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/fees/update/<int:id>', methods=['POST'])
@login_required
def update_fees(id):
    f = RegistrationFee.query.get(id)
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

@app.route('/admin/cfp/button/update/<int:id>', methods=['POST'])
@login_required
def update_cfp_button(id):
    b = CFPButton.query.get(id)
    b.label, b.url = request.form['label'], request.form['url']
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)