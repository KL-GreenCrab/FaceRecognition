from flask import Flask, render_template, request, jsonify
import subprocess
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recognize', methods=['GET', 'POST'])
def recognize():
    # Chỉ thực thi subprocess và trả về kết quả khi có POST request
    if request.method == 'POST':
        try:
            # Chạy subprocess và kiểm tra nếu có lỗi
            result = subprocess.run(
                ["python", "faceRecognition.py"],
                text=True, capture_output=True, check=True
            )

            # Nếu subprocess chạy thành công, lấy kết quả nhận diện
            recognized_id = result.stdout.strip()  # Lấy kết quả từ stdout

            # Trả về kết quả nhận diện
            return jsonify({"message": "Nhận diện thành công", "recognized_id": recognized_id})

        except subprocess.CalledProcessError as e:
            # Nếu subprocess có lỗi, trả về lỗi
            return jsonify({"error": "Lỗi khi chạy nhận diện", "details": e.stderr}), 500

        except Exception as e:
            # Xử lý các lỗi khác
            return jsonify({"error": "Lỗi không xác định", "details": str(e)}), 500

    # Trả về giao diện nhận diện (render_template) nếu là GET request
    return render_template('recognition.html')


@app.route('/employee/<face_id>')
def employee_detail(face_id):
    client = MongoClient("mongodb://localhost:27017/")
    db = client['attendance_system']

    # Tìm thông tin nhân viên từ collection `users`
    user = db['users'].find_one({"_id": face_id})

    if not user:
        return render_template('error.html', message="Nhân viên không tồn tại.")

    # Tìm lịch sử chấm công từ collection `attendance_log`
    attendance_logs = list(db['attendance_log'].find({"ID": face_id}))

    # Tính tổng số giờ làm
    total_hours = sum(float(log['Total Hours']) for log in attendance_logs)

    return render_template(
        'employee_detail.html',
        user=user,
        attendance_logs=attendance_logs,
        total_hours=total_hours
    )


@app.route('/attendance_by_date', methods=['GET', 'POST'])
def attendance_by_date():
    if request.method == 'POST':
        date = request.form['date']  # Lấy ngày người dùng nhập
        client = MongoClient("mongodb://localhost:27017/")
        db = client['attendance_system']

        # Lấy danh sách nhân viên làm việc trong ngày đó từ `attendance_log`
        logs = list(db['attendance_log'].find({"Date": date}))

        # Nếu không có ai làm việc trong ngày đó
        if not logs:
            return render_template('attendance_by_date.html', message="Không có người làm trong ngày này.", date=date)

        return render_template('attendance_by_date.html', logs=logs, date=date)

    return render_template('attendance_by_date.html')


@app.route('/logs')
def logs():
    client = MongoClient("mongodb://localhost:27017/")
    db = client['attendance_system']
    logs = db['attendance_log'].find()
    return render_template('logs.html', logs=logs)


if __name__ == '__main__':
    app.run(debug=True)
