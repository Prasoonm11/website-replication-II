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
    category = db.Column(db.String(100), nullable=False) # e.g., Chief Patron
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(200)) # e.g., Chairperson, MUJ
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

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Public Routes ---
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
        cfp_buttons=CFPButton.query.all())

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
        cfp_buttons=CFPButton.query.all())

# --- Committee Management Routes ---

@app.route('/admin/committee/add', methods=['POST'])
@login_required
def add_committee():
    new_member = CommitteeMember(
        category=request.form.get('category'),
        name=request.form.get('name'),
        position=request.form.get('position'),
        sort_order=request.form.get('sort_order', 0)
    )
    db.session.add(new_member)
    db.session.commit()
    flash('Committee member added successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/committee/update/<int:id>', methods=['POST'])
@login_required
def update_committee(id):
    member = CommitteeMember.query.get_or_404(id)
    member.category = request.form.get('category')
    member.name = request.form.get('name')
    member.position = request.form.get('position')
    member.sort_order = request.form.get('sort_order', 0)
    db.session.commit()
    flash('Member updated successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/committee/delete/<int:id>')
@login_required
def delete_committee(id):
    member = CommitteeMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Member removed.')
    return redirect(url_for('admin'))

# --- Rest of CRUD (Speaker, Date, Fees, CFP, Contacts) ---
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
    return render_template('admin.html',
        speakers=Speaker.query.all(),
        dates=ImportantDate.query.all(),
        committee=CommitteeMember.query.order_by(CommitteeMember.sort_order).all(),
        fees=RegistrationFee.query.all(),
        contacts=ContactInfo.query.all(),
        cfp_sections=CFPSection.query.order_by(CFPSection.sort_order).all(),
        cfp_points=CFPPoint.query.all(),
        cfp_buttons=CFPButton.query.all())

# --- Management Routes ---
@app.route('/admin/add_speaker', methods=['POST'])
@login_required
def add_speaker():
    image_file = request.files.get('image')
    image_url = None
    if image_file and image_file.filename != '':
        blob_response = put(secure_filename(image_file.filename), image_file.read())
        image_url = blob_response['url']
    db.session.add(Speaker(name=request.form['name'], affiliation=request.form['affiliation'], bio=request.form['bio'], image_url=image_url))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_speaker/<int:id>')
@login_required
def delete_speaker(id):
    db.session.delete(Speaker.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

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

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/reset_all')
def reset_all():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('12345')))
    db.session.commit()
    return "Database reset! You can now add committee members in /admin."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)