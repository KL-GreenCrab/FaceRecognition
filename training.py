import os
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, classification_report
from facenet_pytorch import InceptionResnetV1, MTCNN
from sklearn.preprocessing import LabelEncoder
import joblib
from PIL import Image
from torchvision import transforms

# Đường dẫn đến thư mục chứa dữ liệu khuôn mặt
dataset_path = "datasets/"

# Tải mô hình FaceNet
facenet_model = InceptionResnetV1(pretrained='vggface2').eval()
mtcnn = MTCNN(keep_all=True, post_process=False)

# Tăng cường dữ liệu cho ảnh
transform_augment = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
])

# Hàm tạo vector đặc trưng từ ảnh khuôn mặt
def get_face_embedding(model, face_img_path, augment=False):
    img = Image.open(face_img_path).convert('RGB')
    if augment:
        img = transform_augment(img)  # Áp dụng tăng cường dữ liệu
    img_cropped = mtcnn(img)
    if img_cropped is not None:
        img_cropped = img_cropped[0].unsqueeze(0)
        embedding = model(img_cropped)
        return embedding.detach().numpy()[0]
    return None

# Tạo dữ liệu và nhãn từ ảnh
X = []
y = []

for label in os.listdir(dataset_path):
    label_path = os.path.join(dataset_path, label)
    if not os.path.isdir(label_path):
        continue
    for face_img_name in os.listdir(label_path):
        face_img_path = os.path.join(label_path, face_img_name)
        embedding = get_face_embedding(facenet_model, face_img_path, augment=True)
        if embedding is not None:
            X.append(embedding)
            y.append(label)

X = np.array(X)
y = np.array(y)

# Giảm chiều dữ liệu với PCA
pca = PCA(n_components=100)
X_pca = pca.fit_transform(X)

# Mã hóa nhãn
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Chia dữ liệu thành tập huấn luyện và tập kiểm tra
X_train, X_test, y_train, y_test = train_test_split(X_pca, y_encoded, test_size=0.2, random_state=42)

# Sử dụng GridSearchCV để tìm tham số tốt nhất cho SVM
param_grid = {'C': [0.1, 1, 10, 100], 'kernel': ['linear', 'rbf']}
svm_model = GridSearchCV(SVC(probability=True), param_grid, cv=5)
svm_model.fit(X_train, y_train)

# Đánh giá trên tập kiểm tra
y_pred = svm_model.predict(X_test)

# Đánh giá hiệu suất
accuracy = accuracy_score(y_test, y_pred)
print(f"Độ chính xác (accuracy): {accuracy * 100:.2f}%")
print("\nBáo cáo phân loại (classification report):")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Lưu mô hình SVM, bộ mã hóa nhãn và PCA để sử dụng trong tương lai
joblib.dump(svm_model, "face_recognition_svm_model.joblib")
joblib.dump(label_encoder, "label_encoder.joblib")
joblib.dump(pca, "pca_transform.joblib")
