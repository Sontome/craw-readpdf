import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os
import re
import pandas as pd
from datetime import datetime

def convert_date(date_str):
    """Chuyển từ dạng 'Jun 28, 2025' sang '28/06/2025'"""
    try:
        return datetime.strptime(date_str, "%b %d, %Y").strftime("%d/%m/%Y")
    except:
        return None

def read_pdf_first_page(pdf_path, lang="vie"):
    """Đọc trang 1 của PDF, nếu scan thì dùng OCR"""
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if text and text.strip():
            return text

    print(f"📄 {pdf_path} là PDF scan → OCR...")
    pages = convert_from_path(pdf_path, first_page=0, last_page=0)
    return pytesseract.image_to_string(pages[0], lang=lang)

def extract_flight_info(text):
    """Lọc thông tin từ text PDF"""

    # PNR
    pnr_match = re.search(r"([A-Z0-9]{6})\s*$", text, re.MULTILINE)

    # Tên (ưu tiên "Tên:" nếu không có thì fallback từ 'Thông tin hành khách')
    ten_match = re.search(r"Tên:\s*([A-Z ,]+)", text)
    if ten_match:
        ten = ten_match.group(1).replace(",", "").strip()
    else:
        hanh_khach_match = re.search(r"2\..*?Thông tin hành khách.*?\n([A-Z ,]+)", text, re.S)
        ten = hanh_khach_match.group(1).replace(",", "").strip() if hanh_khach_match else None

    # Ngày đặt
    date_booking_match = re.search(r"Ngày đặt:\s*([0-9/]+)", text)

    # Email
    email_match = re.search(r"Email\s+(\S+@\S+)", text)

    # Thông tin chuyến bay (2 chiều)
    flight_info = re.findall(r"(VJ\d+)\s+([A-Za-z]{3} \d{1,2}, \d{4}).*?(\d{2}:\d{2})", text)

    return {
        "PNR": pnr_match.group(1) if pnr_match else None,
        "Tên": ten,
        "Ngày đặt": date_booking_match.group(1) if date_booking_match else None,
        "Email": email_match.group(1) if email_match else None,
        "Ngày đi": convert_date(flight_info[0][1]) if len(flight_info) > 0 else None,
        "Giờ đi": flight_info[0][2] if len(flight_info) > 0 else None,
        "Số máy bay đi": flight_info[0][0] if len(flight_info) > 0 else None,
        "Ngày về": convert_date(flight_info[1][1]) if len(flight_info) > 1 else None,
        "Giờ về": flight_info[1][2] if len(flight_info) > 1 else None,
        "Số máy bay về": flight_info[1][0] if len(flight_info) > 1 else None
    }

def process_pdf_folder(folder_path, output_csv):
    """Xử lý toàn bộ PDF trong folder, lưu kết quả ra CSV"""
    all_data = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"🔍 Đang xử lý: {filename}")
            try:
                text = read_pdf_first_page(pdf_path)
                info = extract_flight_info(text)
                info["File"] = filename
                all_data.append(info)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {filename}: {e}")

    df = pd.DataFrame(all_data)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Xong! Kết quả lưu tại: {output_csv}")

if __name__ == "__main__":
    folder = input("📂 Nhập đường dẫn thư mục chứa PDF: ").strip()
    output_file = os.path.join(folder, "ket_qua.csv")
    process_pdf_folder(folder, output_file)
