# my_app/api/scan_invoice.py
import frappe

@frappe.whitelist()
def get_item_by_barcode(barcode):
    # bypass permission check for read-only lookup
    print("----------------------------------")
    barcode_row = frappe.db.get_value(
        "Item Barcode",
        {"barcode": barcode.strip()},
        ["parent as item_code"],
        as_dict=True
    )
    if not barcode_row:
        return None

    item = frappe.get_doc("Item", barcode_row.item_code)
    return {"item_code": item.item_code, "item_name": item.item_name}
