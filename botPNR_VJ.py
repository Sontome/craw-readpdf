from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests

# ======== CONFIG ========
SPREADSHEET_ID = "1rldpFXT4yrsCy6hKfRVkKpncTsEh0VBeF9LtLLF5hP4"  # ID của file Google Sheet
RANGE_NAME = "VJcheck!A2:Z"  # Lấy từ hàng 2, cột A trở đi
API_URL = "https://thuhongtour.com/vj/checkpnr?pnr={pnr}"

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

            # Lấy thông tin theo format yêu cầu
            phone = data["passengers"][0]["phonenumber"]
            email = data["passengers"][0]["email"]
            fullname = f"{data['passengers'][0]['lastName']} {data['passengers'][0]['firstName']}"
            departure = data["chieudi"]["departure"]
            arrival = data["chieudi"]["arrival"]
            loaive = data["chieudi"]["loaive"]
            giocatcanh = data["chieudi"]["giocatcanh"]
            ngaycatcanh = data["chieudi"]["ngaycatcanh"]
            sohieumaybay = data["chieudi"]["sohieumaybay"]
            if "chieuve" in data and data["chieuve"]:
                departure_ve = data["chieuve"]["departure"]
                arrival_ve = data["chieuve"]["arrival"]
                loaive_ve = data["chieuve"]["loaive"]
                giocatcanh_ve = data["chieuve"]["giocatcanh"]
                ngaycatcanh_ve = data["chieuve"]["ngaycatcanh"]
                sohieumaybay_ve = data["chieuve"]["sohieumaybay"]
                
            else:
                departure_ve = arrival_ve = loaive_ve = giocatcanh_ve = ngaycatcanh_ve = sohieumaybay_ve = None

            updates.append({
                "range": f"VJcheck!B{row_index}:P{row_index}",
                "values": [[phone, email, fullname, departure, arrival, loaive, giocatcanh, ngaycatcanh, sohieumaybay,departure_ve,arrival_ve,loaive_ve,giocatcanh_ve,ngaycatcanh_ve,sohieumaybay_ve]]
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