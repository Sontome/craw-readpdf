from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests

# ======== CONFIG ========
SPREADSHEET_ID = "1rldpFXT4yrsCy6hKfRVkKpncTsEh0VBeF9LtLLF5hP4"  # ID của file Google Sheet
RANGE_NAME = "VNAcheck!A2:Z"  # Lấy từ hàng 2, cột A trở đi
API_URL = "https://thuhongtour.com/vna/checkpnr?pnr={pnr}&ssid=Check"

# Đường dẫn credentials service account
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
for row_index, row in enumerate(values, start=2):  # start=2 vì range bắt đầu từ A2
    pnr = row[0] if len(row) > 0 else ""
    colB = row[1] if len(row) > 1 else ""

    if pnr and not colB:  # Có PNR và cột B trống
        print(f"Đang check PNR: {pnr}")
        try:
            res = requests.post(API_URL.format(pnr=pnr))
            data = res.json()
            print(data)

            phone = data.get("phone", "")
            email = data.get("email", "")
            fullname = data["passengers"][0]["name"] if data.get("passengers") else ""

            row_values = [phone, email, fullname]

            # Lặp qua các chuyến bay và append giá trị động
            for flight in data.get("flights", []):
                row_values.extend([
                    flight.get("nơi_đi", ""),
                    flight.get("nơi_đến", ""),
                    flight.get("loại_vé", ""),
                    flight.get("giờ_đi", ""),
                    flight.get("ngày_đi", ""),
                    flight.get("số_máy_bay", "")
                ])

            # Tạo range động dựa trên số cột
            last_col_letter = chr(ord('B') + len(row_values) - 1)
            updates.append({
                "range": f"VNAcheck!B{row_index}:{last_col_letter}{row_index}",
                "values": [row_values]
            })

        except Exception as e:
            print(f"Lỗi khi check {pnr}: {e}")

# ======== GHI KẾT QUẢ LÊN SHEET ========
if updates:
    body = {
        "valueInputOption": "RAW",
        "data": updates
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    print("✅ Đã cập nhật dữ liệu thành công.")
else:
    print("Không có hàng nào cần cập nhật.")