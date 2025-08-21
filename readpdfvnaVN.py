import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os
import re
import pandas as pd
import json
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

def convert_ddmm(date_str):
    """Chuyển 01Apr2025 thành 01/04/2025"""
    try:
        return datetime.strptime(date_str, "%d%b%Y").strftime("%d/%m/%Y")
    except:
        return date_str  # nếu lỗi thì giữ nguyên

def extract_flight_info(text):
    pnr = re.search(r"Mã đặt chỗ:\s*([A-Z0-9]{6})", text)
    name = re.search(r"Hành khách:\s*(.+?)\s*\(ADT\)", text)
    book_date = re.search(r"Ngày:\s*(\d{1,2}[A-Za-z]{3}\d{4})", text)

    # Bắt số hiệu + giờ khởi hành + ngày (bỏ qua giờ hạ cánh)
    flights = re.findall(
        r"(VN\d+)\s+(\d{2}:\d{2})\s+\d{2}:\d{2}.*?(\d{2}[A-Za-z]{3}\d{4})",
        text,
        re.S
    )

    result = {
        "PNR": pnr.group(1) if pnr else None,
        "Tên": name.group(1).strip() if name else None,
        "Ngày đặt": convert_ddmm(book_date.group(1)) if book_date else None
    }

    for i, f in enumerate(flights, start=1):
        result[f"Ngày đi{i}"] = convert_ddmm(f[2])
        result[f"Giờ đi{i}"] = f[1]
        result[f"Số máy bay đi{i}"] = f[0]

    return result

def process_pdf_folder(folder_path, output_csv, log_file):
    """Xử lý toàn bộ PDF trong folder, lưu kết quả ra CSV và log JSON"""
    all_data = []
    log_data = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"🔍 Đang xử lý: {filename}")
            try:
                text = read_pdf_first_page(pdf_path)
                # Lưu text vào log
                log_data.append({"File": filename, "Text": text})
                
                info = extract_flight_info(text)
                info["File"] = filename
                all_data.append(info)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {filename}: {e}")

    # Lưu CSV
    df = pd.DataFrame(all_data)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    # Lưu log JSON
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Xong! Kết quả lưu tại: {output_csv}")
    print(f"📄 Log text lưu tại: {log_file}")

if __name__ == "__main__":
    folder = input("📂 Nhập đường dẫn thư mục chứa PDF: ").strip()
    output_file = os.path.join(folder, "ket_qua.csv")
    log_file = os.path.join(folder, "log.json")
    process_pdf_folder(folder, output_file, log_file)