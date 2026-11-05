# Face Recognition Demo (Sanitized)

Dự án này đã được làm sạch để loại bỏ ảnh khuôn mặt thật và dữ liệu cá nhân của con người. Tất cả dữ liệu ảnh thực và hồ sơ người dùng có chứa thông tin định danh đã được xóa hoặc thay bằng dữ liệu rỗng.

## Kết quả huấn luyện đã ghi nhận

Sau khi chạy `python training.py`, kết quả thu được là:

```text
Độ chính xác (accuracy): 88.33%

Báo cáo phân loại (classification report):
              precision    recall  f1-score   support

           1       0.90      1.00      0.95         9
           2       0.92      1.00      0.96        11
           3       0.88      0.70      0.78        10
           4       0.67      1.00      0.80         4
           5       0.91      0.91      0.91        11
           6       1.00      0.57      0.73         7
           7       0.89      1.00      0.94         8

    accuracy                           0.88        60
   macro avg       0.88      0.88      0.87        60
weighted avg       0.90      0.88      0.88        60
```

## Cài đặt

```bash
pip install -r requirements.txt
```

Trên Windows nếu console không hiển thị đúng tiếng Việt, hãy chạy:

```powershell
$env:PYTHONIOENCODING='utf-8'
python training.py
```

## Lưu ý về quyền riêng tư

- Không còn chứa ảnh khuôn mặt thật.
- Không còn chứa hồ sơ nhân sự cá nhân như tên, số điện thoại, địa chỉ.
- Mẫu dữ liệu hiện đang ở dạng rỗng hoặc demo, phù hợp để phát triển tiếp mà không lưu trữ dữ liệu cá nhân.
