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

    for item in doc.get("delivery_route_items") or []:
        inv = item.invoice_number
        if not inv: 
            continue

        try:
            invoice = frappe.get_doc("Sales Invoice", inv)

            if doc.workflow_state == "Draft" and invoice.workflow_state == "Packed":
                apply_workflow(invoice, "Dispatch For Delivery")
                invoice.reload()

            elif doc.workflow_state == "Out For Delivery" and invoice.workflow_state == "Dispatched":
                apply_workflow(invoice, "Assign Delivery Route")
                invoice.reload()

            elif doc.workflow_state == "Completed" and invoice.workflow_state == "Out For Delivery":
                apply_workflow(invoice, "Mark As Delivered")
                invoice.reload()

        except Exception as e:
            frappe.log_error(
                title="Delivery Route Invoice Update Error",
                message=f"Failed to update invoice {inv}: {e}"
            )