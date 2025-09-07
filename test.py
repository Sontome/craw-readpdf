import fitz
import re

pdf_path = "input.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
layout = page.get_text("dict")
def find_text_coordinates(layout, search_text):
    """
    Tìm tọa độ (x0, y0) của text trong layout PDF.

    :param layout: dict lấy từ page.get_text("dict")
    :param search_text: chuỗi cần tìm
    :return: list các tọa độ [x0, y0] tìm thấy
    """
    pattern = re.escape(search_text)
    coords = []

    for block in layout.get("blocks", []):
        for line in block.get("lines", []):
            line_text = " ".join(span["text"] for span in line["spans"]).strip()
            if re.search(pattern, line_text):
                x0, y0, _, _ = line["bbox"]
                coords.append([x0, y0])

    return coords
result = find_text_coordinates(layout, "DTYHCZ")
print(result)