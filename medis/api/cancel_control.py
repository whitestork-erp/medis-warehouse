import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def cancel_control(invoice):
    try:
        if not frappe.db.exists("Sales Invoice", invoice):
           return {"ok": False, "doc": None, "msg": f"The invoice {invoice} not found"}
        doc = frappe.get_doc("Sales Invoice", invoice)
        delivery_state = doc.workflow_state
        print("-----------delivery_state----", delivery_state)
        if delivery_state == "Controlling":
           apply_workflow(doc, "Picking Scan")
           print("-------------------SUCCESS-------------------")
           return {"ok": True, "doc": doc}
        return {
			"ok": False,
			"msg": f"The invoice {invoice} is in {delivery_state.upper()} state, cannot cancel control",
		}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
