# my_app/api/scan_invoice.py
import frappe
from frappe.model.workflow import apply_workflow

@frappe.whitelist()
def start_invoice_controlling(invoice):
    try:
        if not frappe.db.exists("Sales Invoice", invoice):
            return {"success": False, "doc": None, "msg": f"The invoice {invoice} not found"}

        doc = frappe.get_doc("Sales Invoice", invoice)
        delivery_state = doc.workflow_state

        if delivery_state == "Picking":
            apply_workflow(doc, "Control Scan")
            doc.custom_controller = frappe.session.user
            doc.save()
            return {"success": True, "doc": doc}
        if delivery_state == "Controlling":
            return {"success": True, "doc": doc}
        return {
            "success": False,
            "msg": f"The invoice {invoice} is already in {delivery_state.upper()} state",
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_invoice_by_barcode")
        return {"success": False, "doc": None, "msg": str(e)}

@frappe.whitelist()
def missing_item_found(invoice):
    doc = frappe.get_doc("Sales Invoice", invoice)
    if doc.custom_first_attempt_miss:
       return
    doc.custom_first_attempt_miss = 1
    doc.save()

@frappe.whitelist()
def get_item_by_barcode(barcode):

    barcode_row = frappe.db.get_value(
        "Item Barcode",
        {"barcode": barcode.strip()},
        ["parent as item_code","parenttype as item_type"],
        as_dict=True
    )

    if not barcode_row:
        return {"success": False, "msg": f"Item with barcode {barcode} not found"}

    if barcode_row.item_type != "Item":
        return {"success": False, "msg": f"Item with barcode {barcode} is not an Item"}

    item = frappe.get_doc("Item", barcode_row.item_code)
    return {"success": True, "item_code": item.item_code, "item_name": item.item_name}

@frappe.whitelist()
def cancel_control(invoice):
    try:
        if not frappe.db.exists("Sales Invoice", invoice):
           return {"success": False, "doc": None, "msg": f"The invoice {invoice} not found"}
        doc = frappe.get_doc("Sales Invoice", invoice)
        delivery_state = doc.workflow_state
        if delivery_state == "Controlling":
           apply_workflow(doc, "Picking Scan")
           return {"success": True, "doc": doc}
        return {
			"success": False,
			"msg": f"The invoice {invoice} is in {delivery_state.upper()} state, cannot cancel control",
		}
    except Exception as e:
        return {"success": False, "msg": str(e)}

@frappe.whitelist()
def pack_invoice(invoice, packages):
    """
    invoice   – Sales Invoice name
    packages  – int
    """
    try:
        doc = frappe.get_doc("Sales Invoice", invoice)
        if doc.workflow_state != "Controlling":
            return {
				"success": False,
				"msg": f"The invoice {invoice} is in {doc.workflow_state.upper()} state, cannot pack",
			}
        doc.custom_packs = packages
        doc.save()
        apply_workflow(doc, "Approve")
        return {"success": True, "msg": f"Invoice {invoice} packed successfully"}
    except Exception as e:
        frappe.log_error(title="Pack Invoice Error", message=str(e))
        return {"success": False, "msg": str(e)}
