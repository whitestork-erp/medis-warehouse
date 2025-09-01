# my_app/api/scan_invoice.py
import frappe
from frappe.model.workflow import apply_workflow


@frappe.whitelist()
def get_invoice_by_barcode(invoice):
    try:
        if not frappe.db.exists("Sales Invoice", invoice):
            return {"ok": False, "doc": None, "msg": f"The invoice {invoice} not found"}
        doc = frappe.get_doc("Sales Invoice", invoice)
        delivery_state = doc.workflow_state

        if delivery_state == "Picking":
            apply_workflow(doc, "Control Scan")
            return {"ok": True, "doc": doc}
        if delivery_state == "Controlling":
            return {"ok": True, "doc": doc}
        return {
            "ok": False,
            "msg": f"The invoice {invoice} is already in {delivery_state.upper()} state",
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_invoice_by_barcode")
        return {"ok": False, "msg": str(e)}
