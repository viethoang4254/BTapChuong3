
import os
import shutil
from datetime import datetime, date  # Sửa import để dùng date.today()
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import schedule
import time
import logging

# Thiết lập logging
logging.basicConfig(filename='backup.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


load_dotenv()

# Sửa tên biến môi trường để khớp với file .env
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
BACKUP_DIR = 'BaiTapVeNha/backups'  # Gán trực tiếp vì không có trong .env
DB_DIR = './BaiTapVeNha'    # Thêm thư mục để tìm file .sql và .sqlite3

# Kiểm tra xem các biến có được load đúng không
if not all([SENDER_EMAIL, APP_PASSWORD, RECEIVER_EMAIL]):
    print("Lỗi: Không thể load các biến từ file .env. Kiểm tra file .env và tên biến.")
    logging.error("Không thể load các biến từ file .env.")
    exit(1)

# Đảm bảo thư mục tồn tại
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

def backup_database():
    """Tìm kiếm và sao lưu các file database (.sql hoặc .sqlite3)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    success_files = []
    failed_files = []

    try:
        for filename in os.listdir(DB_DIR):  # Tìm trong thư mục databases/
            if filename.endswith(".sql") or filename.endswith(".sqlite3"):
                source_path = os.path.join(DB_DIR, filename)
                destination_path = os.path.join(BACKUP_DIR, f"{filename}_{timestamp}")
                try:
                    shutil.copy2(source_path, destination_path)
                    success_files.append(filename)
                    print(f"Đã backup thành công: {filename} -> {destination_path}")
                    logging.info(f"Backup thành công: {filename} -> {destination_path}")
                except Exception as e:
                    failed_files.append(filename)
                    print(f"Lỗi khi backup {filename}: {e}")
                    logging.error(f"Lỗi khi backup {filename}: {str(e)}")
    except Exception as e:
        print(f"Lỗi khi truy cập thư mục {DB_DIR}: {e}")
        logging.error(f"Lỗi khi truy cập thư mục {DB_DIR}: {str(e)}")

    return success_files, failed_files

def send_email(subject, body):
    """Gửi email thông báo."""
    try:
        message = MIMEText(body)
        message['From'] = SENDER_EMAIL
        message['To'] = RECEIVER_EMAIL
        message["Subject"] = subject

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        
        print("Đã gửi email thông báo thành công.")
        logging.info("Gửi email thông báo thành công.")
        return True
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
        logging.error(f"Lỗi khi gửi email: {str(e)}")
        return False

def main():
    """Thực hiện backup và gửi email thông báo."""
    success_files, failed_files = backup_database()

    if success_files or failed_files:
        subject = f"Kết quả Backup Database ngày {date.today()}"
        body = f"Backup lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        if success_files:
            body += "Các file database đã được backup thành công:\n"    
            for file in success_files:
                body += f"- {file}\n"
        if failed_files:
            body += "\nCác file database backup thất bại:\n"
            for file in failed_files:
                body += f"- {file}\n"
    else:
        print("Không tìm thấy file database nào để backup.")
        logging.info("Không tìm thấy file database nào để backup.")
        subject = f"Thông báo Backup Database ngày {date.today()}"
        body = f"Backup lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        body += f"Không có file database (.sql hoặc .sqlite3) nào được tìm thấy trong thư mục {DB_DIR}."

    send_email(subject, body)

def backup_hang_ngay():
    """Lên lịch chạy backup hàng ngày vào lúc 00:00."""
    schedule.every().day.at("00:05").do(main)  # Đổi về 00:00 theo yêu cầu
    try:
        while True:
            schedule.run_pending()
            time.sleep(1) 
    except KeyboardInterrupt:
        print("Chương trình đã dừng bởi người dùng (Ctrl+C).")
        logging.info("Chương trình đã dừng bởi người dùng (Ctrl+C).")
        exit(0)

if __name__ == "__main__":
    print("Chương trình backup database hàng ngày đã được khởi động.")
    logging.info("Chương trình backup database hàng ngày đã được khởi động.")
    backup_hang_ngay()