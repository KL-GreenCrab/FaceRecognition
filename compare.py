from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client['attendance_system']

users_to_insert = [
    {
        "id": "1",
        "username": "admin",
        "password": generate_password_hash("admin123"),  # Mã hóa password
        "role": "admin"
    },
    {
        "id": "2",
        "username": "user1",
        "password": generate_password_hash("user123"),  # Mã hóa password
        "role": "user"
    }
]

# Thêm dữ liệu vào collection 'user_login'
db['user_login'].insert_many(users_to_insert)
