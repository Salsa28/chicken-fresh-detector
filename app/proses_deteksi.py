import os
import uuid
import torch
import datetime
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import base64
import cv2
import numpy as np

# Load the model once when the module is loaded
project_directory = os.path.abspath(os.path.dirname(__file__))
model_path = os.path.join(project_directory, 'best.pt')

try:
    yolo_model = YOLO(model_path)
    # Optimasi untuk real-time: set model ke mode eval dan warm-up
    yolo_model.model.eval()
    
    # Warm-up model dengan dummy image untuk mengurangi latency awal
    dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
    _ = yolo_model(dummy_image, conf=0.55, verbose=False)
    print("YOLO model loaded and warmed up successfully.")
except Exception as e:
    print(f"Error loading YOLO model from {model_path}: {e}")
    yolo_model = None

def proses_deteksi_gambar(image_path, save_detection_image=False, save_path=None):
    """
    Melakukan deteksi objek pada gambar yang diberikan menggunakan model YOLO.
    Mengembalikan 'Ayam Sehat', 'Ayam Tiren', atau 'tidak terdeteksi',
    serta gambar hasil deteksi dalam format Base64 (untuk real-time)
    atau jalur file gambar deteksi (untuk upload biasa).

    Args:
        image_path (str): Jalur ke file gambar yang akan dideteksi.
        save_detection_image (bool): Jika True, gambar dengan deteksi akan disimpan ke disk.
        save_path (str, optional): Direktori untuk menyimpan gambar deteksi. Diperlukan jika save_detection_image True.

    Returns:
        tuple: (str: hasil deteksi, str: gambar Base64 atau jalur file gambar deteksi)
    """
    return proses_deteksi_gambar_optimized(image_path, save_detection_image, save_path, is_realtime=False)

def proses_deteksi_gambar_optimized(image_path, save_detection_image=False, save_path=None, is_realtime=False):
    """
    Versi optimized untuk deteksi real-time dengan performa lebih baik.
    Menggunakan confidence score untuk menentukan hasil deteksi yang paling akurat.
    
    Args:
        image_path (str): Path ke file gambar
        save_detection_image (bool): Simpan gambar hasil deteksi
        save_path (str): Path untuk menyimpan hasil
        is_realtime (bool): Mode real-time untuk optimasi khusus
    
    Returns:
        tuple: (hasil_deteksi, gambar_data, detail_deteksi)
    """
    if yolo_model is None:
        return 'error_deteksi: Model tidak dimuat', None, None

    # Confidence threshold yang lebih rendah untuk deteksi yang lebih sensitif
    conf = 0.45 if is_realtime else 0.55
    detected_objects = []  # Menyimpan semua objek yang terdeteksi dengan detail
    processed_image_data = None

    try:
        # Untuk real-time, resize image untuk performa lebih baik
        if is_realtime:
            img = cv2.imread(image_path)
            if img is not None:
                img = cv2.resize(img, (640, 480))  # Ukuran yang sesuai dengan canvas
                cv2.imwrite(image_path, img)

        # Jalankan inferensi dengan optimasi
        results = yolo_model(
            image_path, 
            conf=conf, 
            save=save_detection_image, 
            project=save_path,
            verbose=False,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

        for result in results:
            # Dapatkan gambar dengan bounding box yang lebih tebal dan jelas
            im_array = result.plot(line_width=3, font_size=16)
            im = Image.fromarray(im_array[..., ::-1])  # Konversi BGR ke RGB untuk PIL

            if save_detection_image:
                if hasattr(result, 'save_dir') and result.save_dir:
                    full_saved_image_path = os.path.join(result.save_dir, os.path.basename(image_path))
                    
                    print(f"DEBUG (proses_deteksi): Original image_path: {image_path}")
                    print(f"DEBUG (proses_deteksi): YOLO save_dir: {result.save_dir}")
                    print(f"DEBUG (proses_deteksi): Expected full_saved_image_path: {full_saved_image_path}")

                    if not os.path.exists(full_saved_image_path):
                        print(f"WARNING (proses_deteksi): Saved image not found at expected path: {full_saved_image_path}")
                        found_files = [f for f in os.listdir(result.save_dir) 
                                     if os.path.isfile(os.path.join(result.save_dir, f)) 
                                     and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                        if found_files:
                            full_saved_image_path = os.path.join(result.save_dir, found_files[0])
                            print(f"DEBUG (proses_deteksi): Using first found image in save_dir: {full_saved_image_path}")
                        else:
                            print("ERROR (proses_deteksi): No image files found in YOLO's save_dir.")
                            processed_image_data = None
                            return 'error_deteksi: Gambar hasil tidak ditemukan', None, None

                    static_folder_path = os.path.join(project_directory, 'static')
                    processed_image_data = os.path.relpath(full_saved_image_path, static_folder_path).replace("\\", "/")
                    print(f"DEBUG (proses_deteksi): Calculated relative path for HTML: {processed_image_data}")
            else:
                # Untuk real-time, gunakan JPEG dengan kualitas tinggi
                buffered = BytesIO()
                im.save(buffered, format="JPEG", quality=85, optimize=True)
                processed_image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Proses semua deteksi dengan detail lengkap
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = yolo_model.names[cls_id]
                confidence = float(box.conf[0])

                if class_name in ['ayam segar', 'ayam tiren']:
                    detected_objects.append({
                        'class': class_name,
                        'confidence': confidence,
                        'confidence_percent': round(confidence * 100, 1)
                    })
        
        # PERBAIKAN LOGIKA: Gunakan confidence score untuk menentukan hasil
        ayam_tiren_detections = [obj for obj in detected_objects if obj['class'] == 'ayam tiren']
        ayam_segar_detections = [obj for obj in detected_objects if obj['class'] == 'ayam segar']
        
        # Cari confidence tertinggi untuk masing-masing kelas
        max_tiren_conf = max([obj['confidence'] for obj in ayam_tiren_detections]) if ayam_tiren_detections else 0
        max_segar_conf = max([obj['confidence'] for obj in ayam_segar_detections]) if ayam_segar_detections else 0
        
        print(f"DEBUG: Max Tiren Confidence: {max_tiren_conf}")
        print(f"DEBUG: Max Segar Confidence: {max_segar_conf}")
        print(f"DEBUG: All detections: {detected_objects}")
        
        # Tentukan hasil berdasarkan confidence tertinggi
        if max_tiren_conf > 0 or max_segar_conf > 0:
            if max_tiren_conf > max_segar_conf:
                # Ayam tiren memiliki confidence lebih tinggi
                if len(ayam_tiren_detections) == 1:
                    final_prediction = "Ayam Tiren"
                else:
                    final_prediction = f"{len(ayam_tiren_detections)} Ayam Tiren"
            else:
                # Ayam segar memiliki confidence lebih tinggi
                if len(ayam_segar_detections) == 1:
                    final_prediction = "Ayam Sehat"
                else:
                    final_prediction = f"{len(ayam_segar_detections)} Ayam Sehat"
        else:
            final_prediction = 'tidak terdeteksi'
        
        # Untuk backward compatibility dengan sistem lama (upload biasa)
        if not is_realtime:
            # Untuk upload biasa, gunakan logika yang sudah diperbaiki
            if max_tiren_conf > max_segar_conf and max_tiren_conf > 0:
                simple_prediction = 'Ayam Tiren'
            elif max_segar_conf > 0:
                simple_prediction = 'Ayam Sehat'
            else:
                simple_prediction = 'tidak terdeteksi'
            
            print(f"DEBUG: Final prediction for upload: {simple_prediction}")
            return simple_prediction, processed_image_data
        
        # Untuk real-time, return detail lengkap
        detection_details = {
            'total_objects': len(detected_objects),
            'ayam_tiren_count': len(ayam_tiren_detections),
            'ayam_segar_count': len(ayam_segar_detections),
            'max_tiren_confidence': max_tiren_conf,
            'max_segar_confidence': max_segar_conf,
            'objects': detected_objects,
            'has_tiren': len(ayam_tiren_detections) > 0,
            'has_segar': len(ayam_segar_detections) > 0
        }
        
        print(f"DEBUG: Final prediction for realtime: {final_prediction}")
        return final_prediction, processed_image_data, detection_details

    except Exception as e:
        print(f"Error during detection in proses_deteksi_gambar_optimized: {e}")
        return 'error_deteksi', None, None
