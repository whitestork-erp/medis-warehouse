import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def transition_to_picking(invoice_barcode):
    """
    Move Sales Invoice from 'Ready For Picking' to 'Picking'
    via workflow transition 'Pick Scan'
    """
    if not frappe.db.exists("Sales Invoice", invoice_barcode):
        return {"ok": False, "msg": f"The invoice {invoice_barcode} not found"}

    doc = frappe.get_doc("Sales Invoice", invoice_barcode)

    if doc.workflow_state != "Ready For Picking":
        return {"ok": False, "msg": f"The invoice {invoice_barcode} is already in state {doc.workflow_state.upper()}"}

    try:
        apply_workflow(doc, "Picking Scan")
        frappe.db.commit()
        return {"ok": True, "msg": f"Moved to {doc.workflow_state}"}
    except Exception as e:
        frappe.log_error(title="Scan Pick Error", message=str(e))
        return {"ok": False, "msg": str(e)}
