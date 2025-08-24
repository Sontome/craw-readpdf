from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
import uvicorn
import os
from backend_read_PDF_VNA_VN import reformat_VNA_VN

from fastapi.responses import FileResponse
app = FastAPI()

@app.post("/process-pdf-vna-vn/")
async def process_pdf_VNA_VN(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    option: str = Form("") # tham số test
           # ví dụ chỉ xử lý 1 page
):
    temp_path = f"VN{file.filename}"
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Tạo đường dẫn file output
    

    # Gọi hàm xử lý PDF, truyền thêm param nếu cần
    reformat_VNA_VN(temp_path, new_text=option)
    

    # Xoá file input nếu không cần giữ
    if os.path.exists(temp_path):
        os.remove(temp_path)
    background_tasks.add_task(os.remove, "output"+temp_path)
    # Trả file PDF đã xử lý về cho client
    return FileResponse(
        path="output"+temp_path,
        filename=f"{file.filename}",
        media_type="application/pdf"
    )