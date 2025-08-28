# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.workflow.doctype.workflow_action.workflow_action import apply_workflow

class DeliveryRoute(Document):
	pass

def update_invoice_states(doc, method):
    """Sync invoices to route state."""
    if not doc.workflow_state:
        return


    invoices = doc.get("delivery_route_items") or []
    action= ""
    print("----------doc.workflow_state----------",doc.workflow_state)
    if doc.workflow_state == "Ready For Delivery1":
        action = "Assign Delivery Route"
    elif doc.workflow_state == "Out For Delivery":
        action = "Assign Delivery Route"
    elif doc.workflow_state == "Delivered":
        action = "Deliver"
    elif doc.workflow_state == "Canceled":
        action = "Cancel"
    elif doc.workflow_state == "Packed":
        action = "Pack"
    if not action:
        return
    print("-----------action",action)
    for item in doc.get("delivery_route_items") or []:
        inv = item.invoice_number
        if not inv:
            continue
        invoice = frappe.get_doc("Sales Invoice", inv)
        print("INVOICE.         _-------", invoice.workflow_state)
        apply_workflow(invoice, action)
        invoice.reload()
    #     try:
    #         invoice = frappe.get_doc("Sales Invoice", inv)
    #         if doc.workflow_state == "Ready For Delivery" or doc.workflow_state == "Out For Delivery" or doc.workflow_state == "Delivered" or doc.workflow_state == "Canceled" or doc.workflow_state == "Packed":
    #            action = ""
	# 		elif
    #         # if doc.workflow_state == "Draft" and invoice.workflow_state == "Packed":
    #         #     apply_workflow(invoice, "Dispatch For Delivery")
    #         #     invoice.reload()

    #         # elif doc.workflow_state == "Out For Delivery" and invoice.workflow_state == "Dispatched":
    #         #     apply_workflow(invoice, "Assign Delivery Route")
    #         #     invoice.reload()

    #         # elif doc.workflow_state == "Completed" and invoice.workflow_state == "Out For Delivery":
    #         #     apply_workflow(invoice, "Mark As Delivered")
    #         #     invoice.reload()

    #     except Exception as e:
    #         frappe.log_error(
    #             title="Delivery Route Invoice Update Error",
    #             message=f"Failed to update invoice {inv}: {e}"
    #         )
