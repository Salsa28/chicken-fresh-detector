import sys
sys.path.insert(0,'/home/zulfa/flask-app/Deteksi-penyakit-mata-pada-anak-YOLOv8')
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the base directory (root of the project)
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set the path to the yolo executable
yolo_path = os.path.join(base_dir, 'env', 'bin')

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

from app import app as application