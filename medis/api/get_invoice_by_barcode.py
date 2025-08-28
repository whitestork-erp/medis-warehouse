# my_app/api/scan_invoice.py
import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def get_invoice_by_barcode(invoice):
    try:
        doc = frappe.get_doc("Sales Invoice", invoice)

        delivery_state = doc.workflow_state

        if delivery_state != "Picking":
            return None
        apply_workflow(doc, "Control Scan")
        return doc
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_invoice_by_barcode")
        return None
    # item = frappe.get_doc("Item", doc.item_code)
    # return {"item_code": item.item_code, "item_name": item.item_name}
