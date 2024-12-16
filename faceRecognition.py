import cv2
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
import joblib
from datetime import datetime
from PIL import Image
from collections import Counter
import time
from pymongo import MongoClient
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Tải các mô hình và công cụ đã lưu
svm_model = joblib.load("face_recognition_svm_model.joblib")
label_encoder = joblib.load("label_encoder.joblib")
pca = joblib.load("pca_transform.joblib")

# Tải mô hình FaceNet và MTCNN để phát hiện và trích xuất đặc trưng khuôn mặt
facenet_model = InceptionResnetV1(pretrained='vggface2').eval()
mtcnn = MTCNN(keep_all=False, post_process=False)

# Khởi tạo kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['attendance_system']
attendance_log = db['attendance_log']
users_collection = db['users']

# Hàm trích xuất vector đặc trưng từ ảnh khuôn mặt


def get_face_embedding(model, img):
    img_cropped = mtcnn(img)
    if img_cropped is not None:
        img_cropped = img_cropped.unsqueeze(0)
        embedding = model(img_cropped)
        return embedding.detach().numpy()[0]
    return None

# Hàm cập nhật chấm công


def update_attendance(face_id):
    face_id = str(face_id + 1)
    print(face_id)
    user = users_collection.find_one({"ID": face_id})
    if user:
        name = user["name"]
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        time_str = current_time.strftime("%H:%M:%S")

        # Kiểm tra nếu đã có bản ghi chấm công cho người này trong ngày hôm nay
        attendance_entry = attendance_log.find_one(
            {"ID": face_id, "Date": date_str})

        if attendance_entry:
            # Nếu đã có giờ vào, kiểm tra giờ ra
            if "Time Out" not in attendance_entry or attendance_entry["Time Out"] is None:
                # Cập nhật giờ ra và tính tổng giờ làm
                time_in = datetime.strptime(
                    attendance_entry["Time In"], "%H:%M:%S")
                time_out = datetime.strptime(time_str, "%H:%M:%S")
                # Tính tổng giờ làm
                total_hours = (time_out - time_in).total_seconds() / 3600

                attendance_log.update_one(
                    {"ID": face_id, "Date": date_str},  # Điều kiện tìm bản ghi
                    # Cập nhật thông tin
                    {"$set": {"Time Out": time_str,
                              "Total Hours": round(total_hours, 2)}}
                )

                # print(f"Chấm công cho {
                #       name} - Giờ ra: {time_str} - Tổng giờ làm: {round(total_hours, 2)} giờ")
                return True  # Thoát nếu đã cập nhật giờ ra
            # else:
            #     print(f"Nhân viên {name} đã có giờ ra trong ngày.")
        else:
            # Nếu chưa có giờ vào, ghi giờ vào
            new_entry = {
                # "_id": face_id,
                "Name": name,
                "Date": date_str,
                "Time In": time_str,
                "Time Out": None,
                "Total Hours": None
            }
            # Kiểm tra nếu bản ghi đã tồn tại trước khi chèn
            attendance_log.update_one(
                {"ID": face_id, "Date": date_str},  # Điều kiện tìm bản ghi
                {"$setOnInsert": new_entry},  # Chỉ chèn nếu chưa có bản ghi
                upsert=True  # Nếu không tìm thấy bản ghi, MongoDB sẽ tạo mới
            )
            # print(f"Chấm công cho {name} - Giờ vào: {time_str}")
            return True  # Không thoát
    # else:
        # print(f"Không tìm thấy thông tin cho ID {face_id}.")
    return False


# Khởi động webcam
cam = cv2.VideoCapture(0)
# print("\n [INFO] Đang khởi động camera... Nhấn 'q' để thoát.")

# Bộ đếm nhận diện
face_counter = Counter()
start_time = time.time()

while True:
    ret, frame = cam.read()
    if not ret:
        # print("[ERROR] Không thể đọc từ webcam.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)

    # Trích xuất đặc trưng từ ảnh khuôn mặt
    embedding = get_face_embedding(facenet_model, img)
    if embedding is not None:
        embedding_pca = pca.transform([embedding])
        prediction = svm_model.predict(embedding_pca)
        face_id = prediction[0]
        worker_name = label_encoder.inverse_transform([face_id])[0]

        # Cập nhật bộ đếm nhận diện
        face_counter[face_id] += 1

        # Hiển thị nhãn nhận diện lên ảnh
        cv2.putText(frame, f"ID: {worker_name}", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    else:
        cv2.putText(frame, "Không nhận diện được khuôn mặt",
                    (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Kiểm tra xem đã qua 5 giây chưa
    if time.time() - start_time > 5:
        # Sau 5 giây, tìm ID nhận diện nhiều nhất
        most_common_id, _ = face_counter.most_common(1)[0]

        # Cập nhật chấm công
        if update_attendance(most_common_id):
            break

        # Reset lại bộ đếm và thời gian
        face_counter.clear()
        start_time = time.time()

    cv2.imshow("Recognition", frame)

    # Thoát nếu nhấn phím 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# print("\n [INFO] Đang thoát chương trình...")

cam.release()
cv2.destroyAllWindows()
