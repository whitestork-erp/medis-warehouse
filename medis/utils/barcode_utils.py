import frappe
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from PIL import Image

@frappe.whitelist()
def generate_barcode(*args, **kwargs):
    # Remove unwanted * before generating
    docname = (kwargs.get("docname") or args[0]).replace("*", "")
    CODE128 = barcode.get_barcode_class("code128")

    buffer = BytesIO()
    options = {
        "module_width": 0.15,   # narrower bars
        "module_height": 5,    # shorter height
        "quiet_zone": 1,        # less margin
        "font_size": 1,         # no text
        "text_distance": 0,
        "background": "white",
        "foreground": "black",
        "write_text":False
    }

    CODE128(docname, writer=ImageWriter()).write(buffer, options)

    # Convert to transparent background
    buffer.seek(0)
    img = Image.open(buffer).convert("RGBA")

    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            newData.append((255, 255, 255, 0))  # transparent
        else:
            newData.append(item)
    img.putdata(newData)

    buffer_out = BytesIO()
    img.save(buffer_out, format="PNG")

    encoded = base64.b64encode(buffer_out.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"
