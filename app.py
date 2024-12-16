from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# Khởi tạo Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Thay bằng secret_key bảo mật hơn

# Khởi tạo Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['attendance_system']

# User Model


class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Hàm load user cho Flask-Login


@login_manager.user_loader
def load_user(user_id):
    user_data = db['user_login'].find_one({"id": user_id})
    if user_data:
        return User(
            id=user_data['id'],
            username=user_data['username'],
            password=user_data['password'],
            role=user_data['role']
        )
    return None

# Route: Trang chủ


@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return render_template('index_admin.html')
    return render_template('index.html')

# Route: Đăng nhập


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = db['user_login'].find_one({"username": username})
        if user_data and check_password_hash(user_data['password'], password):
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                password=user_data['password'],
                role=user_data['role']
            )
            login_user(user)
            return redirect(url_for('index'))

        return render_template('login.html', message="Tên đăng nhập hoặc mật khẩu không đúng!")
    return render_template('login.html')

# Route: Đăng xuất


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route: Quản lý nhân viên (Admin only)


@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Bạn không có quyền truy cập trang này!", 403
    users = list(db['user_login'].find({}, {"_id": 0, "password": 0}))
    return render_template('admin.html', users=users)

# Route: Tạo user mới vào collection user_login (Admin only)


@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return "Bạn không có quyền thực hiện chức năng này!", 403

    data = request.form
    # Kiểm tra ID có tồn tại trong collection users không
    user_info = db['users'].find_one({"ID": data['id']})
    if not user_info:
        return "Không tìm thấy thông tin người dùng!", 404

    # Hash mật khẩu
    hashed_password = generate_password_hash(data['password'])

    # Thêm thông tin người dùng vào user_login
    new_user = {
        "id": data['id'],
        "username": data['username'],
        "name": user_info['name'],  # Lấy tên từ users
        "phone": user_info['phone'],    # Lấy số điện thoại từ users
        "password": hashed_password,
        "role": data['role']
    }
    db['user_login'].insert_one(new_user)
    return redirect(url_for('admin_dashboard'))


# Route: Xem thông tin nhân viên
@app.route('/employee/<face_id>')
@login_required
def employee_detail(face_id):
    user = db['users'].find_one({"ID": face_id})
    if not user:
        return "Nhân viên không tồn tại!", 404

    attendance_logs = list(db['attendance_log'].find({"ID": face_id}))
    total_hours = sum(float(log.get('Total Hours', 0))
                      for log in attendance_logs)

    return render_template(
        'employee_detail.html',
        user=user,
        attendance_logs=attendance_logs,
        total_hours=round(total_hours, 2)
    )

# Route: Danh sách nhân viên và tổng giờ làm


@app.route("/employee")
@login_required
def employees_summary():
    users = list(db['users'].find({}, {"_id": 0}))
    attendance_log = db['attendance_log']

    for user in users:
        user_id = user.get("ID")
        logs = list(attendance_log.find({"ID": user_id}))
        total_hours = sum(float(log.get('Total Hours', 0)) for log in logs)
        user["Total Hours"] = round(total_hours, 2)

    return render_template("employee1.html", employees=users)

# Route: Log chấm công


@app.route('/logs')
@login_required
def logs():
    logs = list(db['attendance_log'].find({}, {"_id": 0}))
    return render_template('logs.html', logs=logs)

# Route: Tìm kiếm chấm công theo ngày


@app.route('/attendance_by_date', methods=['GET', 'POST'])
@login_required
def attendance_by_date():
    if request.method == 'POST':
        date = request.form['date']
        logs = list(db['attendance_log'].find({"Date": date}))
        if not logs:
            return render_template('attendance_by_date.html', message="Không có dữ liệu ngày này.", date=date)
        return render_template('attendance_by_date.html', logs=logs, date=date)

    return render_template('attendance_by_date.html')

# Route: Xóa người dùng


@app.route('/delete_user/<user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return "Bạn không có quyền thực hiện chức năng này!", 403

    result = db['user_login'].delete_one({'id': user_id})
    if result.deleted_count == 0:
        return "Không tìm thấy người dùng!", 404

    return redirect(url_for('admin_dashboard'))

# Route: Chỉnh sửa người dùng


@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return "Bạn không có quyền thực hiện chức năng này!", 403

    user_data = db['user_login'].find_one({"id": user_id})
    if not user_data:
        return "Không tìm thấy người dùng!", 404

    if request.method == 'POST':
        updated_data = {
            "username": request.form['username'],
            "password": generate_password_hash(request.form['password']),
            "role": request.form['role']
        }
        db['user_login'].update_one({"id": user_id}, {"$set": updated_data})
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user_data)


# Chạy ứng dụng Flask
if __name__ == '__main__':
    app.run(debug=True)
