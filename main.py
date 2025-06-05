from app import app, db, bcrypt,Rekomendasi,User,Role
import flask_bcrypt
import os
from dotenv import load_dotenv
# Menjalankan Flask dengan SSL adhoc
#app.run(ssl_context='adhoc')
# Load environment variables from .env file
load_dotenv()

# Get the base directory (root of the project)
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set the path to the yolo executable
yolo_path = os.path.join(base_dir, 'env', 'Scripts', 'yolo.exe')

# Set the environment variable PATH
os.environ['PATH'] += os.pathsep + yolo_path

# Set environment variables for matplotlib and ultralytics
matplotlib_cache_dir = os.path.join(base_dir, 'env', 'matplotlib_cache')
ultralytics_config_dir = os.path.join(base_dir, 'env', 'Ultralytics_config')

os.environ['MPLCONFIGDIR'] = matplotlib_cache_dir
os.environ['YOLO_CONFIG_DIR'] = ultralytics_config_dir

print("Updated PATH:", os.environ['PATH'])
print("MPLCONFIGDIR:", os.environ['MPLCONFIGDIR'])
print("YOLO_CONFIG_DIR:", os.environ['YOLO_CONFIG_DIR'])

if __name__ == '__main__':
    # Tambahkan user dan admin awal
    with app.app_context():
        db.create_all()
        # Ensure roles exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()

        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
            db.session.commit()

        # Ensure admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
            admin_user = User(username="admin", password=hashed_password, verify_email=True,full_name="adminnn",email="admin@gmail.com",phone_number="08123456789")
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()

        # Ensure regular user exists
        regular_user = User.query.filter_by(username='user').first()
        if not regular_user:
            hashed_password = bcrypt.generate_password_hash("user123").decode('utf-8')
            regular_user = User(username="user", password=hashed_password, verify_email=True,full_name="userrr",email="user@gmail.com",phone_number="08123456789")
            regular_user.roles.append(user_role)
            db.session.add(regular_user)
            db.session.commit()
 
        # Membuat rekomendasi mata sehat
        rekomendasi_data = [
            {
                "nama_penyakit": "sehat",
                "pengobatan": """tidak terdeteksi kejanggalan pada mata anak. <br> tetap jaga kesehatan mata anak anda ...""",
                "link_gmaps": "/tips"
            },
            {
                "nama_penyakit": "strabismus (mata juling)",
                "pengobatan": """Terjadi karena tidak keseimbangan dan keharmonisan gerak otot otot bola mata (Ketika otot mata mengalami underaksi dan over aksi sehingga menyebabkan mata juling<br>
Bisa terjadi karena keturunan atau bawaan lahir, Masalah penglihatan pada satu mata, Jika salah satu mata memiliki masalah penglihatan yang signifikan, seperti rabun jauh atau rabun dekat yang tidak terkoreksi.<br>
<br>
Cara mengatasi :<br>
1.	Menggunakan Penutup mata (patching) tersedia di apotik : Metode ini melibatkan menutupi mata yang lebih kuat untuk mendorong mata yang lebih lemah bekerja lebih keras. Ini sering digunakan pada anak-anak untuk membantu memperkuat otot-otot mata yang lebih lemah.<br>
2.	Jika masalah terus berlanjut segera periksakan ke dokter,untuk mendapat penanganan lebih lanjut""",
                "link_gmaps": "klinik"
            },
            {
                "nama_penyakit": 'ptosis (kelopak mata turun)',
                "pengobatan": """Suatu keadaan dimana keadaan kelopak mata atas turun kebawah dari kedudukan mata normal,kedudukan normal itu ditepi kelopak mata kita 2 mm di dekat tepian mata atas,biasanya terjadi pada satu atau dua mata biasanya terjadi tanpa gejala.Akibatnya biasanya terkena gangguan lapang pandang,kesulitan melihat jauh atau dekat atau keadaan paling parah bisa terjadi mata malas pada anak<br>
Cara mengatasinya<br>
                1.	Penyebabnya biasanya terjadi bayi baru lahir atau bawaan terjadi karena otot otot untuk menikan kelopak mata sangat lemah<br>
2.	bisa juga terjadi karena adanya penyakit bawaan seperti tumor.<br>
Untuk ptosis sendiri memang tindakanya hanya oprasi saja,karena ditujukan untuk mengembalikan kelopak matanya seperti semula lagi,segera cari klinik mata terdekat untuk konsultasi dengan dokter
""",
                "link_gmaps": "klinik"
            },
            {
                "nama_penyakit":'mata merah',
                "pengobatan": """Mata merah biasanya terjadi karena infeks iatau alergi Paparan asap, debu, angin, atau bahan kimia yang dapat menyebabkan mata merah<br>
Cara mengatasinya<br>
1.	Pastikan apakah mata yang terkena kemerahan hanya satu atau keduanya, karena jika hanya satu mata, kemungkinan besar terjadi infeksi.<br>
2.	Perhatikan apakah mata yang merah disertai dengan adanya belekan. Jika mata merah disertai belekan, dapat diteteskan antibiotik tetes mata yang tidak mengandung steroid, yang dapat dibeli di apotek terdekat. Jika kondisi ini berlanjut, segera kunjungi klinik terdekat dan konsultasikan dengan dokter.<br>
""",
                "link_gmaps": "apotek,klinik"
            },
            {
                "nama_penyakit": 'mata bengkak',
                "pengobatan": """Mata bengkak pada anak dapat disebabkan oleh berbagai factor seperti reaksi alergi terhadap debu, bulu hewan, atau bahan kimia dalam produk seperti sabun atau sampo dapat menyebabkan mata bengkak, gatal, dan berair,gigitan serangga atau saluran air mata tersumbat.<br>
Cara mengatasinya<br>
Kompres dingin:<br>
Gunakan kain bersih yang dibasahi dengan air dingin dan letakkan di atas mata yang bengkak selama beberapa menit. <br>
Hindari menyentuh atau menggosok mata:<br>
Ajari anak untuk tidak menggosok atau menyentuh matanya agar tidak memperburuk kondisi.<br>
Obat antihistamin:<br>
Jika pembengkakan disebabkan oleh alergi, obat antihistamin dapat membantu. Namun, pastikan untuk berkonsultasi dengan dokter sebelum memberikan obat ini kepada anak.<br>
Rekomendasi klinik terdekat""",
                "link_gmaps": "klinik,apotek"
            },
            {
                "nama_penyakit": 'mata bintitan',
                "pengobatan": """Mata bintitan (hordeolum) pada anak adalah kondisi di mana terjadi pembengkakan kecil, berwarna merah, dan terasa sakit di kelopak mata. Ini biasanya disebabkan oleh infeksi bakteri pada kelenjar minyak atau folikel bulu mata. <br>
Jangan mencoba memencet atau memecahkan bintitan, karena dapat memperburuk infeksi atau menyebarkannya ke area lain.<br>
<br>
Cara mengatasi :<br>
1.	Membeli salep atau tetes mata antibiotik di apotik untuk mengatasi infeksi.<br>
2.	Jika bintitan tidak sembuh dalam beberapa hari, terasa sangat sakit, atau disertai demam, segera bawa anak ke dokter untuk mendapatkan penanganan lebih lanjut.""",
                "link_gmaps": "klinik,apotek"
            }
        ]

        for rekomendasi in rekomendasi_data:
            if not Rekomendasi.query.filter_by(nama=rekomendasi['nama_penyakit']).first():
                new_rekomendasi = Rekomendasi(
                    nama=rekomendasi['nama_penyakit'],
                    pengobatan=rekomendasi['pengobatan'],
                    link_rekomendasi=rekomendasi['link_gmaps']
                )
                db.session.add(new_rekomendasi)
                db.session.commit()

    app.run(host="0.0.0.0", debug=True, port=4040)

