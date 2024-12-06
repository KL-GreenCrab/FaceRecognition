import os
import cv2
import numpy as np
from mtcnn import MTCNN
from pymongo import MongoClient

# Khởi tạo MongoDB client và truy cập database
client = MongoClient("mongodb://localhost:27017/")
db = client['attendance_system']
users_collection = db['users']

# Khởi tạo bộ phát hiện khuôn mặt với MTCNN
face_detector = MTCNN()

# Nhập ID khuôn mặt và thông tin người dùng
face_id = input('\n Nhập ID khuôn mặt <return> ==>  ')
name = input('Nhập tên người dùng: ')
phone = input('Nhập số điện thoại: ')
address = input('Nhập địa chỉ: ')

# Kiểm tra nếu người dùng đã tồn tại trong MongoDB
if not users_collection.find_one({"_id": face_id}):
    # Lưu thông tin người dùng vào MongoDB
    user_data = {
        "_id": face_id,
        "name": name,
        "phone": phone,
        "address": address
    }
    users_collection.insert_one(user_data)
    print(f"Đã thêm người dùng vào MongoDB: {name}")
else:
    print(f"Người dùng với ID {face_id} đã tồn tại.")

# Tạo thư mục cho ID nếu chưa tồn tại
dataset_path = f"datasets/{face_id}"
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

print('\n [INFO] Khởi tạo camera...')

# Khởi động webcam
cam = cv2.VideoCapture(0)
count = 0

while True:
    ret, img = cam.read()
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Chuyển ảnh về RGB cho FaceNet
    faces = face_detector.detect_faces(rgb_img)
    
    for face in faces:
        x, y, w, h = face['box']
        
        # Căn chỉnh và cắt khuôn mặt
        face_img = rgb_img[y:y+h, x:x+w]
        face_img = cv2.resize(face_img, (160, 160))  # FaceNet yêu cầu kích thước 160x160

        count += 1

        # Lưu ảnh vào thư mục tương ứng với face_id
        file_name = f"{dataset_path}/User.{face_id}.{count}.jpg"
        cv2.imwrite(file_name, cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))  # Lưu ảnh ở định dạng BGR

        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.imshow('image', img)

    # Thoát khi nhấn phím 'q' hoặc đã thu thập đủ ảnh
    k = cv2.waitKey(200) & 0xff
    if k == 27:
        break
    elif count >= 45:
        break

print('\n Thoát')
cam.release()
cv2.destroyAllWindows()
