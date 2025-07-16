from . import app,db,History,Rekomendasi,User,bcrypt,login_role_required
from flask import render_template, request, jsonify, redirect, url_for,session,g,abort
from io import BytesIO
import os,textwrap, locale, json, uuid, time,re
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy import extract
from datetime import datetime
from sqlalchemy.orm import aliased

#halaman homepage
@app.route('/')
def index():
    return render_template('index.html')
#halaman tips
@app.route('/tips')
def userberita():
    # tips = Berita.query.all()
    return render_template('tips.html')
#halaman dashboard user
@app.route('/user/dashboard')
@login_role_required('user')
def dashboarduser():
    if not all([session.get('username'), session.get('full_name'), session.get('email')]):
        return redirect(url_for("profile"))
    else:
        # Ambil satu data toko user yang aktif (atau pertama)
        
        return render_template('user/dashboard.html')
#halaman profile
@app.route('/user/profile')
@login_role_required('user')
def profile():
    return render_template('user/profile.html')

@app.route('/user/update_profile', methods=['POST'])
@login_role_required('user')
def update_profile():
    user = User.query.filter_by(id=session['id']).first()
    data = request.get_json()
    new_full_name = data.get('full_name')
    new_address = data.get('address')
    new_email = data.get('email')
    new_phone_number = data.get('phone_number')

    try:
        # Update user fields only if they are provided and different from current values
        if new_full_name and new_full_name != user.full_name:
            if User.query.filter(User.username == new_full_name, User.id != user.id).first():
                return jsonify({"msg": "nama lengkap already taken"}), 400
            if User.query.filter(User.full_name == new_full_name, User.id != user.id).first():
                return jsonify({"msg": "nama lengkap already taken"}), 400
            user.full_name = new_full_name

        if new_email and new_email != user.email:
            if user.query.filter(user.email == new_email, user.user_id != user.id).first():
                return jsonify({"msg": "Email already taken"}), 400
            user.email = new_email

        if new_address and new_address != user.address:
            user.address = new_address


        db.session.commit()

        # Update session with new data
        session['full_name'] = user.full_name
        session['address'] = user.address
        session['email'] = user.email

        if not all([user.username, user.full_name, user.email]):
            return jsonify({"msg": "Silakan lengkapi semua data dahulu sebelum bisa mengakses fitur-fitur kami"}), 400

        return jsonify({"msg": "Profil berhasil diperbarui"})

    except IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig)  # Extract the original error message
        return jsonify({"msg": f"Error: {error_message}"}), 400
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        return jsonify({"msg": f"Error: {error_message}"}), 400

@app.route('/ganti_password')
@login_role_required('user')
def ganti_password():
    return render_template('ganti_password.html')

@app.route('/ganti_password', methods=["POST"])
@login_role_required('user')
def ganti_password_post():
    # Coba ambil data dari JSON
    data = request.get_json()
    if data:
        password_lama = data.get('password_lama')
        password_baru = data.get('password_baru')
    else:
        # Jika tidak ada data JSON, ambil dari form
        password_lama = request.form('password_lama')
        password_baru = request.form('password_baru')
    user = User.query.filter_by(username=session['username']).first()
    if user:
        if bcrypt.check_password_hash(user.password, password_lama):
            # Mengganti password lama dengan password baru
            user.password = bcrypt.generate_password_hash(password_baru).decode('utf-8')
            db.session.commit()
            return jsonify({"msg": "Berhasil Update Password"})
        else:
            return jsonify({"msg": "Password lama salah"})
    else:
        return jsonify({"msg": "user tidak ditemukan"})

@app.route('/user/hasil_deteksi/<id>')
@login_role_required('user')
def user_hasil_deteksi(id):
    if 'full_name' not in session:
        abort(403)  # Forbidden, user tidak terautentikasi

    # Query data history berdasarkan id dan username dari session
    history_record = History.query.filter_by(id=id).first()
    if not history_record:
        abort(404)  # Not found, data history tidak ditemukan
    
    # Pastikan hasil_deteksi adalah dictionary
    hasil_deteksi_str = history_record.hasil_deteksi

    hasil_deteksi = hasil_deteksi_str.split(",")

    if hasil_deteksi[-1] == '':
        hasil_deteksi.pop()
    print(hasil_deteksi)
    # Query semua rekomendasi
    rekomendasi_records = Rekomendasi.query.all()
    print(rekomendasi_records)
    rekomendasi_list = [record.serialize() for record in rekomendasi_records]
    print(rekomendasi_list)

    # Gabungkan rekomendasi yang relevan dengan hasil diagnosa
    rekomendasi_deteksi = {}
    for deteksi in hasil_deteksi:
        for rekomendasi in rekomendasi_list:
            if rekomendasi['nama'] == deteksi:
                rekomendasi_deteksi[deteksi] = rekomendasi
    print(rekomendasi_deteksi)
    # Query semua rekomendasi
    user = User.query.filter_by(id=history_record.user_id).first()
   
    deteksi = {
        'nama_user': user.full_name,
        'tanggal_deteksi': history_record.tanggal_deteksi,
        'file_deteksi': history_record.file_deteksi,
        'hasil_deteksi': hasil_deteksi,
        'rekomendasi_deteksi': rekomendasi_deteksi,
    }
    print(deteksi)

    return render_template('user/hasil_deteksi.html', deteksi=deteksi)

@app.route('/user/history_deteksi', methods=['GET'])
@login_role_required('user')
def user_history_deteksi():
    filter_date = request.args.get('filterDate')
    filter_month = request.args.get('filterMonth')
    filter_year = request.args.get('filterYear')
    filter_complete_date = request.args.get('filterCompleteDate')
    filter_anything = request.args.get('filteranything')  # Filter baru untuk "apapun"

    # Generate list of years from 2000 to current year
    current_year = datetime.now().year
    years = list(range(2000, current_year + 1))

    # List of months with values 1-12 in Indonesian
    months = [
        {"name": "Januari", "value": 1},
        {"name": "Februari", "value": 2},
        {"name": "Maret", "value": 3},
        {"name": "April", "value": 4},
        {"name": "Mei", "value": 5},
        {"name": "Juni", "value": 6},
        {"name": "Juli", "value": 7},
        {"name": "Agustus", "value": 8},
        {"name": "September", "value": 9},
        {"name": "Oktober", "value": 10},
        {"name": "November", "value": 11},
        {"name": "Desember", "value": 12},
    ]

    query = History.query.filter_by(user_id=session["id"])

    if filter_complete_date:
        query = query.filter(func.date(History.tanggal_deteksi) == filter_complete_date)
    else:
        if filter_date:
            query = query.filter(extract('day', History.tanggal_deteksi) == filter_date)
        if filter_month:
            query = query.filter(extract('month', History.tanggal_deteksi) == filter_month)
        if filter_year:
            query = query.filter(extract('year', History.tanggal_deteksi) == filter_year)
    
    # Aliased untuk tabel-tabel yang ingin di-join
   
    user_alias = aliased(User)

    if filter_anything:
       
        query = query.join(user_alias, History.user_id == user_alias.id)\
                    .filter(
            db.or_(
            
                History.tanggal_deteksi.ilike(f'%{filter_anything}%'),
                History.hasil_deteksi.ilike(f'%{filter_anything}%'),
                user_alias.full_name.ilike(f'%{filter_anything}%')
            )
        )
    
    histori_records = query.all()
    deteksi_records = []

    for history_record in histori_records:
        
        deteksi = {
            'id': history_record.id,
            'nama_user': session["full_name"],          
            'hasil_deteksi': history_record.hasil_deteksi,
            'tanggal_deteksi': history_record.tanggal_deteksi.strftime('%Y-%m-%d'),
        }
        deteksi_records.append(deteksi)
    
    return render_template('user/history_deteksi.html', 
                        histori_records=deteksi_records, 
                        years=years, 
                        months=months)
