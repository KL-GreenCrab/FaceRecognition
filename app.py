from flask import Flask, render_template, request, jsonify
import subprocess
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recognize', methods=['GET', 'POST'])
def recognize():
    if request.method == 'POST':
        try:
            result = subprocess.run(
                ["python", "faceRecognition.py"],
                text=True, capture_output=True, check=True
            )
            recognized_id = result.stdout.strip()
            return jsonify({"message": "Nhận diện thành công", "recognized_id": recognized_id})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Lỗi khi chạy nhận diện", "details": e.stderr}), 500
        except Exception as e:
            return jsonify({"error": "Lỗi không xác định", "details": str(e)}), 500

    return render_template('recognition.html')


@app.route('/employee/<face_id>')
def employee_detail(face_id):
    client = MongoClient("mongodb://localhost:27017/")
    db = client['attendance_system']
    attendance_logs = list(db['attendance_log'].find({"ID": face_id}))

    if not attendance_logs:
        return render_template('error.html', message="Không có dữ liệu chấm công cho mã demo này.")

    total_hours = sum(float(log['Total Hours']) for log in attendance_logs)
    return render_template(
        'employee_detail.html',
        face_id=face_id,
        attendance_logs=attendance_logs,
        total_hours=total_hours
    )


@app.route('/attendance_by_date', methods=['GET', 'POST'])
def attendance_by_date():
    if request.method == 'POST':
        date = request.form['date']
        client = MongoClient("mongodb://localhost:27017/")
        db = client['attendance_system']
        logs = list(db['attendance_log'].find({"Date": date}))

        if not logs:
            return render_template('attendance_by_date.html', message="Không có dữ liệu trong ngày này.", date=date)

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
