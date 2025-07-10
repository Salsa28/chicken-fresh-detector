from . import app, db,allowed_file, History,Rekomendasi,login_role_required,DataToko,User
from flask import render_template, request, jsonify, redirect, url_for,session,g,abort,flash
import os,textwrap, locale, json, uuid, time,re
from io import BytesIO
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy import extract
from sqlalchemy.orm import aliased
  
#halaman admin
@app.route('/admin/dashboard')
@login_role_required('admin')
def dashboardadmin():
    return render_template('admin/dashboard.html')
#halaman history konsultasi
@app.route('/admin/history_deteksi')
@login_role_required('admin')
def history_deteksi():
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
        query = query.filter(func.date(History.tanggal_deteksi) == filter_complete_date)
    else:
        if filter_date:
            query = query.filter(extract('day', History.tanggal_deteksi) == filter_date)
        if filter_month:
            query = query.filter(extract('month', History.tanggal_deteksi) == filter_month)
        if filter_year:
            query = query.filter(extract('year', History.tanggal_deteksi) == filter_year)
    
    # Aliased untuk tabel-tabel yang ingin di-join
    data_toko_alias = aliased(DataToko)
    user_alias = aliased(User)

    if filter_anything:
        query = query.join(data_toko_alias, History.datatoko_id == data_toko_alias.id)\
                    .join(user_alias, History.user_id == user_alias.id)\
                    .filter(
            db.or_(
                data_toko_alias.nama_toko.ilike(f'%{filter_anything}%'),
                History.tanggal_deteksi.ilike(f'%{filter_anything}%'),
                History.hasil_deteksi.ilike(f'%{filter_anything}%'),
                user_alias.full_name.ilike(f'%{filter_anything}%')
            )
        )
    
    histori_records = query.all()
    deteksi_records = []

    for history_record in histori_records:
        data_toko = DataToko.query.filter_by(id=history_record.datatoko_id).first()
        user = User.query.filter_by(id = history_record.user_id).first()
        deteksi = {
            'id': history_record.id,
            'nama_user': user.full_name,
            'nama_toko': data_toko.nama_toko if data_toko else "Data Toko Tidak Ditemukan",
            'tanggal_deteksi': history_record.tanggal_deteksi.strftime('%Y-%m-%d'),
            'hasil_deteksi': history_record.hasil_deteksi,
        }
        deteksi_records.append(deteksi)
    
    return render_template('admin/history_deteksi.html', histori_records=deteksi_records, years=years, months=months)

@app.route('/admin/history_deteksi/<int:id>', methods=['PUT'])
@login_role_required('admin')
def detail_history_deteksi(id):
    history_record = History.query.get_or_404(id)
    data = request.get_json()

    # Update fields with data from JSON request
    history_record.tanggal_deteksi = data.get('tanggal_deteksi')
    history_record.hasil_deteksi = data.get('hasil_deteksi')

    db.session.commit()

    # Return JSON response
    return jsonify({'msg': 'History updated successfully!'})

@app.route('/admin/history_deteksi/<int:id>/delete', methods=['DELETE'])
@login_role_required('admin')
def delete_history_deteksi(id):
    history_record = History.query.get_or_404(id)
    db.session.delete(history_record)
    db.session.commit()
    return jsonify({'msg': 'History deleted successfully!'})

#halaman deteksi terbanyak
@app.route('/admin/deteksi_terbanyak')
@login_role_required('admin')
def deteksi_terbanyak():
    # Daftar nama deteksi
    names = ["Ayam Tiren", "Ayam Segar"]

    # Inisialisasi jumlah kasus dengan 0 untuk setiap nama
    jml_kasus = [0] * len(names)

    # Ambil data dari database
    history_records = History.query.all()

    # Hitung jumlah kasus untuk setiap deteksi
    for record in history_records:
        hasil_deteksi = record.hasil_deteksi  # Sesuaikan dengan struktur data Anda
        for index, deteksi in enumerate(names):
            if deteksi in hasil_deteksi:  # Sesuaikan dengan cara Anda menyimpan data deteksi
                jml_kasus[index] += 1
            else:
                jml_kasus[1] += 1

    return render_template('admin/deteksi_terbanyak.html', names=names, jml_kasus=jml_kasus)
# Setelah proses penghitungan selesai, data dihitung kemudian dikirim ke template HTML deteksi_terbanyak.html menggunakan fungsi render_template.
# Template HTML akan menerima dua variabel: names dan jml_kasus, yang kemudian dapat digunakan untuk menampilkan data di halaman web.

#halaman hasil deteksi
@app.route('/admin/history_konsultasi/<id>')
@login_role_required('admin')
def admin_hasil_deteksi(id):
    # Query data history berdasarkan id
    history_record = History.query.filter_by(id=id).first()
    if not history_record:
        abort(404)  # Not found, data history tidak ditemukan
    
    # Query user terkait
    user_record = User.query.filter_by(id=history_record.user_id).first()
    if not user_record:
        abort(404)  # Not found, data user tidak ditemukan

    # Query data Toko terkait
    # data_toko = DataToko.query.filter_by(id=history_record.datatoko_id).first()
    # if not data_toko:
    #     abort(404)  # Not found, data Toko tidak ditemukan
    
    # Pastikan hasil_deteksi adalah string dan ubah menjadi list
    hasil_deteksi_str = history_record.hasil_deteksi or ""
    hasil_deteksi = [deteksi.strip() for deteksi in hasil_deteksi_str.split(",") if deteksi.strip()]


    # rekomendasi yang relevan dengan hasil deteksi
    rekomendasi_deteksi = {}
    for deteksi in hasil_deteksi:
        print(deteksi)
        rekomendasi_deteksi[deteksi] = deteksi
    
    # Membuat dictionary diagnosa untuk dikirim ke template
    deteksi = {
        'nama_user': user_record.full_name,
        # 'nama_toko': data_toko.nama_toko,
        'tanggal_deteksi': history_record.tanggal_deteksi,
        'file_deteksi': history_record.file_deteksi,
        'hasil_deteksi': hasil_deteksi,
        'rekomendasi_deteksi': rekomendasi_deteksi,
    }

    # Kirim data ke template untuk ditampilkan
    return render_template('user/hasil_deteksi.html', deteksi=deteksi)

