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
from werkzeug.utils import secure_filename # Import ini untuk secure_filename

# Import fungsi deteksi Anda dari proses_deteksi.py
from .proses_deteksi import proses_deteksi_gambar 

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
        return render_template('user/dashboard.html')
    
# Halaman tips memasak ayam yang baru
@app.route('/tips-memasak-ayam')
def tips_memasak_ayam():
    return render_template('tips_memasak_ayam.html')

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
    print(f"DEBUG (api_user): file_deteksi from DB for ID {id}: {history_record.file_deteksi}")
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

# --- ENDPOINT UNTUK UPLOAD GAMBAR BIASA (DENGAN PENYIMPANAN RIWAYAT) ---
@app.route('/predict', methods=['POST'])
@login_role_required('user')
def predict():
    if 'gambar' not in request.files:
        return jsonify({'msg': 'Tidak ada file gambar yang diunggah'}), 400

    file = request.files['gambar']
    if file.filename == '':
        return jsonify({'msg': 'Tidak ada file gambar yang dipilih'}), 400

    if file:
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'upload'))
        detect_folder = app.config.get('DETECT_FOLDER', os.path.join(app.root_path, 'static', 'detect'))
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        if not os.path.exists(detect_folder):
            os.makedirs(detect_folder)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        try:
            # Panggil fungsi deteksi dari proses_deteksi.py
            # save_detection_image=True untuk menyimpan gambar hasil deteksi ke disk
            prediction_result, detected_image_filepath = proses_deteksi_gambar(
                filepath, 
                save_detection_image=True, 
                save_path=detect_folder 
            )
            print(f"DEBUG (api_user): Path to be saved in DB: {detected_image_filepath}")

            if prediction_result == 'error_deteksi':
                raise Exception("Deteksi gagal atau model tidak dimuat.")

            # Simpan riwayat ke database
            new_history = History(
                user_id=session['id'],
                tanggal_deteksi=datetime.now(),
                # Simpan path relatif dari project_directory agar bisa diakses di frontend
                file_deteksi=detected_image_filepath, 
                hasil_deteksi=prediction_result 
            )
            db.session.add(new_history)
            db.session.commit()

            # Hapus file asli yang diunggah setelah diproses
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'msg': 'SUKSES',
                'id_hasil': new_history.id 
            }), 200
        except Exception as e:
            db.session.rollback() 
            app.logger.error(f"Error during prediction (regular upload): {e}")
            if os.path.exists(filepath):
                os.remove(filepath) 
            return jsonify({'msg': f'Terjadi kesalahan saat deteksi: {str(e)}'}), 500
    
    return jsonify({'msg': 'Terjadi kesalahan tidak dikenal'}), 500

# --- ENDPOINT BARU UNTUK DETEKSI REAL-TIME (TANPA PENYIMPANAN RIWAYAT) ---
@app.route('/predict_realtime', methods=['POST'])
@login_role_required('user') 
def predict_realtime():
    if 'gambar' not in request.files:
        return jsonify({'msg': 'Tidak ada file gambar yang diunggah'}), 400

    file = request.files['gambar']
    if file.filename == '':
        return jsonify({'msg': 'Tidak ada file gambar yang dipilih'}), 400

    if file:
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'upload'))
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        try:
            # Panggil fungsi deteksi dari proses_deteksi.py
            # save_detection_image=False karena ini real-time, tidak perlu menyimpan setiap frame ke disk
            prediction_result, encoded_image = proses_deteksi_gambar(filepath, save_detection_image=False)

            if prediction_result == 'error_deteksi':
                raise Exception("Deteksi gagal atau model tidak dimuat.")

            # Hapus file sementara setelah deteksi
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'msg': 'SUKSES',
                'prediction': prediction_result, # Mengembalikan hasil prediksi
                'image_data': encoded_image # Mengembalikan gambar Base64
            }), 200
        except Exception as e:
            app.logger.error(f"Error during real-time prediction: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'msg': f'Terjadi kesalahan saat deteksi: {str(e)}'}), 500
    
    return jsonify({'msg': 'Terjadi kesalahan tidak dikenal'}), 500
