
import frappe
from frappe.model.workflow import apply_workflow,get_common_transition_actions


@frappe.whitelist()
def pack_invoice(invoice, packages, items):
    """
    invoice   – Sales Invoice name
    packages  – int
    items     – dict  {item_code: qty}
    """
    print("===================",items)
    try:
        doc = frappe.get_doc("Sales Invoice", invoice)
        # doc_info = frappe.get_doc("Sales Invoice", invoice)
        print("---------------cos",doc.workflow_state)
        # res = get_common_transition_actions(doc,"Sales Invoice")
        # print("---------------res",res)
        doc.custom_packs = packages
        apply_workflow(doc, "Approve")
        print("---------------Approve",doc)
        # doc.save(ignore_permissions=True)
        return {"success": True}
    except Exception as e:
        frappe.log_error(title="Pack Invoice Error", message=str(e))
        return {"success": False, "error": str(e)}
