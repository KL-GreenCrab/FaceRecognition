import os
import cv2
from mtcnn import MTCNN
from pymongo import MongoClient

# MongoDB is only used for anonymous demo IDs, not personal information.
client = MongoClient("mongodb://localhost:27017/")
db = client['attendance_system']
users_collection = db['users']

face_detector = MTCNN()
face_id = input('\n Nhập ID khuôn mặt <return> ==>  ')

# Do not store the real person's name, phone number, or address.
if not users_collection.find_one({"_id": face_id}):
    users_collection.insert_one({"_id": face_id, "demo_only": True})
    print(f"Đã thêm mẫu demo với ID: {face_id}")
else:
    print(f"Mẫu demo với ID {face_id} đã tồn tại.")

dataset_path = f"datasets/{face_id}"
os.makedirs(dataset_path, exist_ok=True)

print('\n [INFO] Khởi tạo camera...')
cam = cv2.VideoCapture(0)
count = 0

while True:
    ret, img = cam.read()
    if not ret:
        break

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = face_detector.detect_faces(rgb_img)

    for face in faces:
        x, y, w, h = face['box']
        face_img = rgb_img[y:y + h, x:x + w]
        face_img = cv2.resize(face_img, (160, 160))

        count += 1
        file_name = f"{dataset_path}/User.{face_id}.{count}.jpg"
        cv2.imwrite(file_name, cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))

        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.imshow('image', img)

    k = cv2.waitKey(200) & 0xff
    if k == 27 or count >= 45:
        break

print('\n Thoát')
cam.release()
cv2.destroyAllWindows()
