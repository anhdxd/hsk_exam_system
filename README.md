# HSK Exam System

Hệ thống thi HSK (Hanyu Shuiping Kaoshi) được xây dựng bằng Django.

## Tính năng

- Quản lý người dùng và xác thực
- Ngân hàng câu hỏi HSK (cấp độ 1-6)
- Tạo và quản lý kỳ thi
- Làm bài thi trực tuyến với hẹn giờ
- Chấm điểm tự động
- Phân tích kết quả và báo cáo
- Import câu hỏi từ CSV/JSON

## Cài đặt

1. Tạo virtual environment:
```bash
python -m venv hskexamsystem-env
```

2. Kích hoạt virtual environment:
```bash
# Windows
hskexamsystem-env\Scripts\activate

# Linux/Mac
source hskexamsystem-env/bin/activate
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file .env và cấu hình:
```bash
cp .env.example .env
```

5. Chạy migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Tạo superuser:
```bash
python manage.py createsuperuser
```

7. Chạy server:
```bash
python manage.py runserver
```

## Cấu trúc dự án

- `apps/` - Các Django apps
- `config/` - Cấu hình Django
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `media/` - File upload
- `data/` - Dữ liệu mẫu và backup
- `tests/` - Integration tests

## License

MIT License
