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
            admin_user = User(username="admin", password=hashed_password, verify_email=True,full_name="adminnn",email="admin@gmail.com",phone_number="0895383225221")
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()

        # Ensure regular user exists
        regular_user = User.query.filter_by(username='user').first()
        if not regular_user:
            hashed_password = bcrypt.generate_password_hash("user123").decode('utf-8')
            regular_user = User(username="user", password=hashed_password, verify_email=True,full_name="userrr",email="user@gmail.com",phone_number="0895383225221")
            regular_user.roles.append(user_role)
            db.session.add(regular_user)
            db.session.commit()

        
    app.run(host="0.0.0.0", debug=True, port=4040)

