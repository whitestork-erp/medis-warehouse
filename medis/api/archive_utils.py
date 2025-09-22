import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def transition_to_archived(invoice_name):
    """
    Move Sales Invoice from 'Delivered | Canceled' to 'Archived'
    via workflow transition 'Archive'
    """
    if not frappe.db.exists("Sales Invoice", invoice_name):
        return {"ok": False, "msg": f"The invoice {invoice_name} not found"}

    doc = frappe.get_doc("Sales Invoice", invoice_name)

    if doc.workflow_state != "Delivered" and doc.workflow_state != "Canceled":
        return {"ok": False, "msg": f"Cannot archive invoice {invoice_name}, current state {doc.workflow_state.upper()}, should be DELIVERED or CANCELED"}

    try:
        apply_workflow(doc, "Archive")
        return {"ok": True, "msg": f"Moved to {doc.workflow_state}"}
    except Exception as e:
        frappe.log_error(title="Scan Pick Error", message=str(e))
        return {"ok": False, "msg": str(e)}
