from . import app,mysql,db,allowed_file, History,Rekomendasi,login_role_required,DataAnak,User
from flask import render_template, request, jsonify, redirect, url_for,session,g,abort,flash
import os,textwrap, locale, json, uuid, time,re
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy import extract
from sqlalchemy.orm import aliased

@app.before_request
def before_request():
    g.con = mysql.connection.cursor()
@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'con'):
        g.con.close()
        
def do_image(do, table, id):
    try:
        if do == "delete":
            filename = get_image_filename(table, id)
            delete_image(filename)
            return True
        file = request.files['gambar']
        if file is None or file.filename == '':
            return "default.jpg"
        else:
            filename = get_image_filename(table, id)
            delete_image(filename)
            return resize_and_save_image(file, table, id)
    except KeyError:
        if do == "edit":
            if table =="galeri":
                return True
            reset = request.form['reset']
            print(reset)
            if reset=="true":
                g.con.execute(f"UPDATE {table} SET gambar = %s WHERE id = %s", ("default.jpg", id))
                mysql.connection.commit()
        return "default.jpg"# Tangkap kesalahan jika kunci 'gambar' tidak ada dalam request.files
    except FileNotFoundError:
        pass  # atau return "File tidak ditemukan."
    except Exception as e:
        print(str(e))
        return str(e)

def resize_and_save_image(file, table=None, id=None):
    img = Image.open(file).convert('RGB').resize((600, 300))
    img_io = BytesIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    random_name = uuid.uuid4().hex + ".jpg"
    destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
    img.save(destination)
    if table and id:
        g.con.execute(f"UPDATE {table} SET gambar = %s WHERE id = %s", (random_name, id))
        mysql.connection.commit()
        return True
    else:
        return random_name
def get_image_filename(table, id):
    g.con.execute(f"SELECT gambar FROM {table} WHERE id = %s", (id,))
    result = g.con.fetchone()
    if result == "default.jpg":
        return None
    return result[0] if result else None

def delete_image(filename):
    if filename == "default.jpg":
        return True
    if filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(image_path):
            os.remove(image_path)
            
def fetch_data_and_format(query):
    g.con.execute(query)
    data = g.con.fetchall()
    column_names = [desc[0] for desc in g.con.description]
    info_list = [dict(zip(column_names, row)) for row in data]
    return info_list
            
#halaman admin
@app.route('/admin/dashboard')
@login_role_required('admin')
def dashboardadmin():
    return render_template('admin/dashboard.html')
#halaman history konsultasi
@app.route('/admin/history_konsultasi')
@login_role_required('admin')
def history_konsultasi():
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

    query = History.query

    if filter_complete_date:
        query = query.filter(func.date(History.tanggal_konsultasi) == filter_complete_date)
    else:
        if filter_date:
            query = query.filter(extract('day', History.tanggal_konsultasi) == filter_date)
        if filter_month:
            query = query.filter(extract('month', History.tanggal_konsultasi) == filter_month)
        if filter_year:
            query = query.filter(extract('year', History.tanggal_konsultasi) == filter_year)
    
    # Aliased untuk tabel-tabel yang ingin di-join
    data_anak_alias = aliased(DataAnak)
    user_alias = aliased(User)

    if filter_anything:
        query = query.join(data_anak_alias, History.dataanak_id == data_anak_alias.id)\
                    .join(user_alias, History.user_id == user_alias.id)\
                    .filter(
            db.or_(
                data_anak_alias.nama_anak.ilike(f'%{filter_anything}%'),
                data_anak_alias.usia_anak.ilike(f'%{filter_anything}%'),
                History.tanggal_konsultasi.ilike(f'%{filter_anything}%'),
                History.hasil_diagnosa.ilike(f'%{filter_anything}%'),
                user_alias.full_name.ilike(f'%{filter_anything}%')
            )
        )
    
    histori_records = query.all()
    diagnosa_records = []

    for history_record in histori_records:
        data_anak = DataAnak.query.filter_by(id=history_record.dataanak_id).first()
        user = User.query.filter_by(id = history_record.user_id).first()
        diagnosa = {
            'id': history_record.id,
            'nama_user': user.full_name,
            'nama_anak': data_anak.nama_anak if data_anak else "Data Anak Tidak Ditemukan",
            'usia_anak': data_anak.usia_anak if data_anak else "N/A",
            'tanggal_konsultasi': history_record.tanggal_konsultasi.strftime('%Y-%m-%d'),
            'hasil_diagnosa': history_record.hasil_diagnosa,
        }
        diagnosa_records.append(diagnosa)
    
    return render_template('admin/history_konsultasi.html', histori_records=diagnosa_records, years=years, months=months)

@app.route('/admin/history_konsultasi/<int:id>', methods=['PUT'])
@login_role_required('admin')
def detail_history_konsultasi(id):
    history_record = History.query.get_or_404(id)
    data = request.get_json()

    # Update fields with data from JSON request
    history_record.tanggal_konsultasi = data.get('tanggal_konsultasi')
    history_record.hasil_diagnosa = data.get('hasil_diagnosa')

    db.session.commit()

    # Return JSON response
    return jsonify({'msg': 'History updated successfully!'})

@app.route('/admin/history_konsultasi/<int:id>/delete', methods=['DELETE'])
@login_role_required('admin')
def delete_history_konsultasi(id):
    history_record = History.query.get_or_404(id)
    db.session.delete(history_record)
    db.session.commit()
    return jsonify({'msg': 'History deleted successfully!'})

#halaman penyakit terbanyak
@app.route('/admin/penyakit_terbanyak')
@login_role_required('admin')
def penyakit_terbanyak():
    # Daftar nama penyakit
    names = ['strabismus (mata juling)', 'ptosis (kelopak mata turun)', 'mata merah', 'mata bengkak', 'mata bintitan']

    # Inisialisasi jumlah kasus dengan 0 untuk setiap nama
    jml_kasus = [0] * len(names)

    # Ambil data dari database
    history_records = History.query.all()

    # Hitung jumlah kasus untuk setiap penyakit
    for record in history_records:
        hasil_diagnosa = record.hasil_diagnosa  # Sesuaikan dengan struktur data Anda
        for index, penyakit in enumerate(names):
            if penyakit in hasil_diagnosa:  # Sesuaikan dengan cara Anda menyimpan data penyakit
                jml_kasus[index] += 1

    return render_template('admin/penyakit_terbanyak.html', names=names, jml_kasus=jml_kasus)
# Setelah proses penghitungan selesai, data dihitung kemudian dikirim ke template HTML penyakit_terbanyak.html menggunakan fungsi render_template.
# Template HTML akan menerima dua variabel: names dan jml_kasus, yang kemudian dapat digunakan untuk menampilkan data di halaman web.

#halaman hasil diagnosa
@app.route('/admin/history_konsultasi/<id>')
@login_role_required('admin')
def admin_hasil_diagnosa(id):
    # Query data history berdasarkan id
    history_record = History.query.filter_by(id=id).first()
    if not history_record:
        abort(404)  # Not found, data history tidak ditemukan
    
    # Query user terkait
    user_record = User.query.filter_by(id=history_record.user_id).first()
    if not user_record:
        abort(404)  # Not found, data user tidak ditemukan

    # Query data anak terkait
    data_anak = DataAnak.query.filter_by(id=history_record.dataanak_id).first()
    if not data_anak:
        abort(404)  # Not found, data anak tidak ditemukan
    
    # Pastikan hasil_diagnosa adalah string dan ubah menjadi list
    hasil_diagnosa_str = history_record.hasil_diagnosa or ""
    hasil_diagnosa = [diagnosis.strip() for diagnosis in hasil_diagnosa_str.split(",") if diagnosis.strip()]

    # Query semua rekomendasi
    rekomendasi_records = Rekomendasi.query.all()
    rekomendasi_list = [record.serialize() for record in rekomendasi_records]

    # Gabungkan rekomendasi yang relevan dengan hasil diagnosa
    rekomendasi_diagnosa = {}
    for penyakit in hasil_diagnosa:
        for rekomendasi in rekomendasi_list:
            if rekomendasi['nama'] == penyakit:
                rekomendasi_diagnosa[penyakit] = rekomendasi
    
    # Membuat dictionary diagnosa untuk dikirim ke template
    diagnosa = {
        'nama_user': user_record.full_name,
        'nama_anak': data_anak.nama_anak,
        'usia_anak': data_anak.usia_anak,
        'tanggal_konsultasi': history_record.tanggal_konsultasi,
        'file_deteksi': history_record.file_deteksi,
        'hasil_diagnosa': hasil_diagnosa,
        'rekomendasi_diagnosa': rekomendasi_diagnosa,
    }

    # Kirim data ke template untuk ditampilkan
    return render_template('user/hasil_diagnosa.html', diagnosa=diagnosa)

