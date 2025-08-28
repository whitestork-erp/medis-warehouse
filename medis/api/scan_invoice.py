import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def transition_to_picking(invoice_barcode):
    """
    Move Sales Invoice from 'Ready For Picking' to 'Picking'
    via workflow transition 'Pick Scan'
    """

    print(":::::::::::::::::::::::::")
    if not frappe.db.exists("Sales Invoice", invoice_barcode):
        return {"ok": False, "msg": "Invoice not found"}

    doc = frappe.get_doc("Sales Invoice", invoice_barcode)

    if doc.workflow_state != "Ready For Picking":
        return {"ok": False, "msg": f"Wrong state: {doc.workflow_state}"}

    try:
        apply_workflow(doc, "Picking Scan")   # exact action name in workflow
        frappe.db.commit()
        return {"ok": True, "msg": f"Moved to {doc.workflow_state}"}
    except Exception as e:
        frappe.log_error(title="Scan Pick Error", message=str(e))
        return {"ok": False, "msg": str(e)}
