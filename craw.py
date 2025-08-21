from __future__ import print_function
import base64
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scope chỉ cần đọc Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def crawl_gmail(sender_email, subject_keyword, save_folder):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Xây query Gmail
    q = f'from:{sender_email} has:attachment filename:pdf'
    if subject_keyword.strip():
        q += f' subject:{subject_keyword}'

    results = service.users().messages().list(userId='me', q=q).execute()
    messages = results.get('messages', [])

    if not messages:
        messagebox.showinfo("Kết quả", "Không tìm thấy email nào phù hợp.")
        return

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    count = 0
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = m['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Không tiêu đề")
        print("Tiêu đề:", subject)

        # Tải file PDF
        parts = m['payload'].get('parts', [])
        for part in parts:
            if part['filename'] and part['filename'].endswith(".pdf"):
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(
                    userId='me', messageId=msg['id'], id=att_id
                ).execute()
                data = base64.urlsafe_b64decode(att['data'].encode('UTF-8'))
                filepath = os.path.join(save_folder, part['filename'])
                with open(filepath, 'wb') as f:
                    f.write(data)
                print("Đã tải:", filepath)
                count += 1

    messagebox.showinfo("Hoàn tất", f"Đã tải {count} file PDF về {save_folder}")

# ================== GIAO DIỆN ==================
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder_selected)

def start_crawl():
    sender_email = entry_sender.get()
    subject_keyword = entry_subject.get()
    save_folder = entry_folder.get()

    if not sender_email or not save_folder:
        messagebox.showerror("Lỗi", "Phải nhập email người gửi và thư mục lưu file")
        return

    crawl_gmail(sender_email, subject_keyword, save_folder)

# Tạo cửa sổ
root = tk.Tk()
root.title("Gmail PDF Crawler")

tk.Label(root, text="Email người gửi:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_sender = tk.Entry(root, width=40)
entry_sender.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Từ khóa trong tiêu đề (tuỳ chọn):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_subject = tk.Entry(root, width=40)
entry_subject.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Thư mục lưu file PDF:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
entry_folder = tk.Entry(root, width=40)
entry_folder.grid(row=2, column=1, padx=5, pady=5)
btn_browse = tk.Button(root, text="Chọn...", command=browse_folder)
btn_browse.grid(row=2, column=2, padx=5, pady=5)

btn_start = tk.Button(root, text="Crawl", command=start_crawl, bg="green", fg="white")
btn_start.grid(row=3, column=0, columnspan=3, pady=10)

root.mainloop()
