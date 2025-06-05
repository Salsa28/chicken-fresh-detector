from . import app,db,bcrypt,jwt,Role,User,mail,s,login_role_required
from itsdangerous import BadSignature, SignatureExpired
import re
from flask import request,render_template,redirect,url_for,jsonify,session,flash,render_template_string
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,unset_jwt_cookies
from flask_mail import Message

@app.route('/tambah_admin')
def tambah():
    return render_template('admin/register.html')
        
# Endpoint untuk membuat token
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"msg": "Invalid request"}), 400

        username = data['username']
        password = data['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "username salah"}), 404
        if not bcrypt.check_password_hash(user.password, password):
            return jsonify({"msg": "password salah"}), 401
        if user.verify_email == False:
            return jsonify({"msg": "anda belum memverifikasi email"}), 401
        user_roles = [role.name for role in user.roles]
        access_token = create_access_token(identity=username)
        session["username"] = username
        session['jwt_token'] = access_token
        session['full_name'] = user.full_name
        session['id'] = user.id
        
        # Redirect berdasarkan peran user
        if 'admin' in user_roles:
            session['role'] = 'admin'
            print(session)
            return jsonify(access_token=access_token, redirect_url=url_for('dashboardadmin'))
        elif 'user' in user_roles:
            session['role'] = 'user'
            session['address'] = user.address
            session['email'] = user.email
            session['phone_number'] = user.phone_number
            print(session)
            if user.full_name == "" or user.email == "" or user.phone_number == "":
                return jsonify(access_token=access_token, redirect_url=url_for('profile'))
            else:
                return jsonify(access_token=access_token, redirect_url=url_for('dashboarduser'))

    return render_template('user/login.html')
# Endpoint yang memerlukan autentikasi
def unset_session():
    response = jsonify({'message': 'Logout berhasil'})
    unset_jwt_cookies(response)
    session.pop('jwt_token', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('id', None)
    session.pop('full_name', None)
    session.pop('address', None)
    session.pop('email', None)
    session.pop('phone_number', None)
@app.route('/keluar')
def keluar():
    # Hapus token dari cookie (anda bisa menghapus token dari header juga jika tidak menggunakan cookie)
    unset_session()
    flash('Sukses Logout')
    return redirect(url_for('login'))

@jwt.expired_token_loader
def expired_token_callback():
    return redirect(url_for('login'))

@app.route('/bikin_akun_admin', methods=['GET', 'POST'])
@login_role_required('admin')
def register_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return jsonify({"msg": "Username and password are required"}), 400
        
        # Check if the username and emaillegreop[d] already exists
        print(username+' | '+password+' | ')
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({"msg": "Username already  exists"}), 400
        email = User.query.filter_by(email=email).first()
        if email:
            return jsonify({"msg": "Email already  exists"}), 400

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Create a new user
        new_user = User(username=username, password=hashed_password, verify_email=True)

        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()
        
        new_user.roles.append(admin_role)
        
        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successfull')
        return redirect(url_for('login', msg='Registration Successful'))

    return render_template('admin/register.html')

# Function to validate email format
def is_valid_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
    return re.match(regex, email)

@app.route('/bikin_akun_user', methods=['POST'])
def register_user():
    data = request.get_json()
    print(data)
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    re_password = data.get('re_password')

    if not username or not email or not password or not re_password:
        return jsonify({"msg": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    if password != re_password:
        return jsonify({"msg": "Passwords do not match"}), 400
    cek_username = User.query.filter_by(username=username).first()
    if cek_username:
        return jsonify({"msg": "Username already exists"}), 400
    cek_email = User.query.filter_by(email=email).first()
    if cek_email:
        return jsonify({"msg": "Username already exists"}), 400
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    # Create a new user
    new_user = User(username=username, password=hashed_password, verify_email=False, full_name='', address='', email=email, phone_number='')
    admin_role = Role.query.filter_by(name='user').first()
    if not admin_role:
        admin_role = Role(name='user')
        db.session.add(admin_role)
        db.session.commit()
    
    new_user.roles.append(admin_role)
    
    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    token = s.dumps(email, salt='email-confirm')

    conf_email_url = url_for('confirm_email', token=token, _external=True)
    email_body = render_template_string('''
        Hello {{ username }},
        
        Anda menerima email ini, karena kami memerlukan verifikasi email untuk akun Anda agar aktif dan dapat digunakan.
        
        Silakan klik tautan di bawah ini untuk verifikasi email Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
        
        confirm youe email: {{ conf_email_url }}
        
        hubungi dukungan jika Anda memiliki pertanyaan.
        
        Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
        
        Salam Hangat,
        
        Admin
    ''', username=username,  conf_email_url=conf_email_url)

    msg = Message('Confirmasi Email Anda',
                  sender='zulfanisa0103@gmail.com', recipients=[email])

    msg.body = email_body
    mail.send(msg)

    flash(" Register berhasil silahkan cek email anda.")

    return jsonify({"msg":'Register Berhasil silahkan cek email anda '})
@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return jsonify({"msg": "Token telah kedaluwarsa"}), 400
    except BadSignature:
        return jsonify({"msg": "Token tidak valid"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Update the verify_email field to True
    user.verify_email = True
    db.session.commit()
    return '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Email Verify</title>
      </head>
      <body>
        <h1>Email Telah Terverifikasi </h1>
      </body>
    </html>
    '''.format(token)
@app.route("/verif_email",methods=["GET","POST"])
def verif_email():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"msg": "Email harus diisi"})
            
        user = User.query.filter_by(email=email).first()
        print(user)
        if not user:
            return jsonify({"msg": "Email tidak ditemukan"})

        verified_user = User.query.filter_by(email=email,verify_email=True).first()
        print(verified_user)
        if verified_user:
            return jsonify({"msg": "user sudah terverifikasi"})

        token = s.dumps(email, salt='email-confirm')

        conf_email_url = url_for('confirm_email', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ username }},
            
            Anda menerima email ini, karena kami memerlukan verifikasi email untuk akun Anda agar aktif dan dapat digunakan.
            
            Silakan klik tautan di bawah ini untuk verifikasi email Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
            
            confirm youe email: {{ conf_email_url }}
            
            hubungi dukungan jika Anda memiliki pertanyaan.
            
            Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
            
            Salam Hangat,
            
            Pejuang D4
        ''', username=user.username,  conf_email_url=conf_email_url)

        msg = Message('Confirmasi Email Anda',
                    sender='zulfanisa0103@gmail.com', recipients=[email])

        msg.body = email_body
        mail.send(msg)

        flash("Silahkan cek email anda.")

        return jsonify({"msg":"Silahkan cek email anda."})
    else:
        return render_template("verif_email.html")
    
@app.route("/forgotpassword",methods=["GET","POST"])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"msg": "Email harus diisi"})
            
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"msg": "Email tidak ditemukan"})

        token = s.dumps(email, salt='reset-password')

        reset_password_url = url_for('reset_password', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ user["name"] }},
            
            Anda menerima email ini, karena kami menerima permintaan untuk mengatur ulang kata sandi akun Anda.
            
            Silakan klik tautan di bawah ini untuk mengatur ulang kata sandi Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
            
            Reset your password: {{ reset_password_url }}
            
            Jika Anda tidak meminta pengaturan ulang kata sandi, abaikan email ini atau hubungi dukungan jika Anda memiliki pertanyaan.
            
            Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
            
            Salam Hangat,
            
            Mriki_Project
        ''', user=user,  reset_password_url=reset_password_url)

        msg = Message('Reset Kata Sandi Anda',
                    sender='zulfanisa0103@gmail.com ', recipients=[email])

        msg.body = email_body
        mail.send(msg)


        return jsonify({"msg": "Email untuk mereset kata sandi telah dikirim."})
    else:
        return render_template("forgot_password.html")


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)
    except SignatureExpired:
        return jsonify({"msg": "Token telah kedaluwarsa"}), 400
    except BadSignature:
        return jsonify({"msg": "Token tidak valid"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')

        # Hash the new password and update it in the database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        flash('Password berhasil direset. Silakan login dengan password baru Anda.')
        return jsonify({"msg": "Sukses"})
    return render_template("reset_password.html",token=token)
