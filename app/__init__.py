from flask import Flask, jsonify, request, session, render_template, send_from_directory, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta, datetime,timezone
from functools import wraps
import os,uuid

app = Flask(__name__)

project_directory = os.path.abspath(os.path.dirname(__file__))

# Define upload and detect folders
upload_folder = os.path.join(project_directory, 'static', 'upload')
detect_folder = os.path.join(project_directory, 'static', 'detect')

# Configure app with folder paths
app.config['UPLOAD_FOLDER'] = upload_folder 
app.config['PROJECT_FOLDER'] = project_directory 
app.config['DETECT_FOLDER'] = detect_folder 

# --- PERBAIKAN: Tambahkan baris ini untuk membuat folder jika belum ada ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    print(f"Created UPLOAD_FOLDER: {app.config['UPLOAD_FOLDER']}")

if not os.path.exists(app.config['DETECT_FOLDER']):
    os.makedirs(app.config['DETECT_FOLDER'])
    print(f"Created DETECT_FOLDER: {app.config['DETECT_FOLDER']}")
# --- Akhir PERBAIKAN ---

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/db_smart_kukuruyuk'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bukan rahasia')
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', b'asahdjhwquoyo192382qo')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'qwdu92y17dqsu81')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id'), nullable=False)

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    verify_email = db.Column(db.Boolean(), default=False)
    roles = db.relationship('Role', secondary='user_roles',
                             backref=db.backref('users', lazy='dynamic'))
    full_name = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

class History(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    hasil_deteksi = db.Column(db.String(255), nullable=True)
    file_deteksi = db.Column(db.String(225), nullable=True)
    tanggal_deteksi = db.Column(db.DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

class Rekomendasi(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    nama = db.Column(db.String(225), unique=True, nullable=False)
    def serialize(self):
        return {
            'id': self.id,
            'nama': self.nama,
        }

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'kukuruyukcare@gmail.com'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'vsxu tuzu geky btjp'))
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])
jwt = JWTManager(app)

# Allow CORS
from flask_cors import CORS
CORS(app)

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return """User-agent: *
    Disallow: /private/
    Disallow: /cgi-bin/
    Disallow: /images/
    Disallow: /pages/thankyou.html
    """

@app.errorhandler(404)
def page_not_found(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'Not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404

@app.route('/invalid')
def invalid():
    abort(404)

def login_role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'id' not in session:
                return redirect(url_for('login'))
            if session.get('role') != required_role:
                return jsonify({"msg": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rute contoh
@app.route('/about')
def about():
    return "About Page"

@app.route('/contact')
def contact():
    return "Contact Page"

@app.route('/blog')
def blog():
    return "Blog Page"

@app.route('/blog/first-post')
def first_post():
    return "First Blog Post"

@app.route('/blog/second-post')
def second_post():
    return "Second Blog Post"

from . import api_user, api_admin, login, proses_deteksi
