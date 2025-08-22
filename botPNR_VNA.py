from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests
import time
from openpyxl.utils import get_column_letter
# ======== CONFIG ========
SPREADSHEET_ID = "1rldpFXT4yrsCy6hKfRVkKpncTsEh0VBeF9LtLLF5hP4"
RANGE_NAME = "VNAcheck!A2:Z"
API_URL = "https://thuhongtour.com/vna/checkpnr?pnr={pnr}&ssid=Check"
SERVICE_ACCOUNT_FILE = "credentials.json"

# ======== AUTH GOOGLE SHEETS ========
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=creds)

# ======== LẤY DỮ LIỆU SHEET ========
sheet = service.spreadsheets()
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME
).execute()

values = result.get("values", [])

if not values:
    print("Không có dữ liệu.")
    exit()

# ======== XỬ LÝ DỮ LIỆU ========
updates = []
for row_index, row in enumerate(values, start=2):
    pnr = row[0].strip() if len(row) > 0 else ""
    colB = row[1] if len(row) > 1 else ""

    if pnr and not colB:
        print(f"Đang check PNR: {pnr}")
        row_values = []  
        status_msg = "OK"

        try:
            res = requests.post(API_URL.format(pnr=pnr), timeout=15)
            if res.status_code != 200 or not res.text.strip():
                raise Exception(f"HTTP {res.status_code}")

            data = res.json()
            if not isinstance(data, dict):
                raise Exception("Data không phải dạng JSON dict")

            phone = data.get("phone", "")
            email = data.get("email", "")
            fullname = ""

            if data.get("passengers") and isinstance(data["passengers"], list) and len(data["passengers"]) > 0:
                fullname = data["passengers"][0].get("name", "")

            row_values = [phone, email, fullname]

            if data.get("flights") and isinstance(data["flights"], list):
                for flight in data["flights"]:
                    row_values.extend([
                        flight.get("nơi_đi", ""),
                        flight.get("nơi_đến", ""),
                        flight.get("loại_vé", ""),
                        flight.get("giờ_đi", ""),
                        flight.get("ngày_đi", ""),
                        flight.get("số_máy_bay", "")
                    ])

        except Exception as e:
            status_msg = f"Lỗi: {e}"
            row_values = ["", "", ""]  # vẫn giữ 3 cột trống khi lỗi

        # Thêm cột trạng thái cuối
        row_values.append(status_msg)

        # Luôn ghi đúng dòng chứa PNR này
        last_col_index = 2 + len(row_values) - 1  # B = cột 2
        last_col_letter = get_column_letter(last_col_index)

        updates.append({
            "range": f"VNAcheck!B{row_index}:{last_col_letter}{row_index}",
            "values": [row_values]
        })

# ======== GHI KẾT QUẢ LÊN SHEET THEO BATCH ========
BATCH_SIZE = 50
if updates:
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        body = {
            "valueInputOption": "RAW",
            "data": batch
        }
        for _ in range(3):
            try:
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body=body
                ).execute()
                print(f"✅ Đã cập nhật {len(batch)} dòng (từ {i+1} đến {i+len(batch)})")
                break
            except Exception as e:
                print(f"❌ Lỗi khi update batch: {e}, thử lại...")
                time.sleep(3)
        time.sleep(5)
else:
    print("Không có hàng nào cần cập nhật.")
