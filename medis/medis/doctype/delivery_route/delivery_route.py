# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.workflow.doctype.workflow_action.workflow_action import apply_workflow
import json

class DeliveryRoute(Document):

	def before_save(self):
		if(self.get("workflow_state") != "Ready For Delivery"): return
		# 1. Get the current list of child row names
		# current_rows = {row.name for row in self.delivery_route_item}          # rows now on the form
		current_items = {row.invoice_number for row in self.delivery_route_item if row.invoice_number}

		# 2. Get the list that was stored at the previous save
		try:
			previous_items = set(json.loads(self.get("_last_child_rows") or "[]"))
		except Exception:
			previous_items = set()

		# 3. Save the current list for the *next* save
		self._last_child_rows = json.dumps(list(current_items))

		# 4. Rows that have just been ADDED
		linked = current_items - previous_items
		for child_name in linked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Ready For Delivery":          # change to your state
				apply_workflow(child_doc, "Prepare For Delivery")             # transition name that moves → "Linked"

		# 5. Rows that have just been REMOVED
		unlinked = previous_items - current_items
		for child_name in unlinked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Packed":
				apply_workflow(child_doc, "Repack")
@frappe.whitelist()
def repack_delivery_route_invoices(delivery_route_name):
    """Repack all sales invoices associated with the delivery route."""
    try:
        # Get the delivery route document
        delivery_route = frappe.get_doc("Delivery Route", delivery_route_name)

        # Get all sales invoices from delivery route items
        cancelled_invoices = []
        failed_invoices = []

        for item in delivery_route.get("delivery_route_item") or []:
            if not item.invoice_number:
                continue

            try:
                # Get the sales invoice document
                invoice = frappe.get_doc("Sales Invoice", item.invoice_number)

                # Check if invoice is not already packed
                if invoice.workflow_state != "Packed":
                    # Apply repack workflow action
                    apply_workflow(invoice, "Repack")
                    invoice.reload()
                    cancelled_invoices.append(item.invoice_number)

            except Exception as e:
                frappe.log_error(
                    title="Failed to Repack Sales Invoice",
                    message=f"Failed to repack invoice {item.invoice_number}: {str(e)}"
                )
                failed_invoices.append(item.invoice_number)

        # Prepare response message
        message = f"Successfully repacked {len(cancelled_invoices)} sales invoices."
        if failed_invoices:
            message += f" Failed to repack {len(failed_invoices)} invoices: {', '.join(failed_invoices)}"

        return {
            "status": "success",
            "message": message,
            "cancelled_invoices": cancelled_invoices,
            "failed_invoices": failed_invoices
        }

    except Exception as e:
        frappe.log_error(
            title="Delivery Route Invoice Cancellation Error",
            message=f"Failed to cancel invoices for delivery route {delivery_route_name}: {str(e)}"
        )
        frappe.throw(f"Failed to cancel sales invoices: {str(e)}")

@frappe.whitelist()
def get_delivery_route_invoices(delivery_route_name):
    """Get all sales invoices associated with the delivery route for delivery management."""
    try:
        # Get the delivery route document
        delivery_route = frappe.get_doc("Delivery Route", delivery_route_name)
        invoices = []

        for item in delivery_route.get("delivery_route_item") or []:
            if not item.invoice_number:
                continue

            try:
                # Get the sales invoice document
                invoice = frappe.get_doc("Sales Invoice", item.invoice_number)

                invoice_data = {
                    "invoice_number": item.invoice_number,
                    "customer": invoice.customer,
                    "customer_name": invoice.customer_name,
                    "grand_total": invoice.grand_total,
                    "workflow_state": invoice.workflow_state,
                    "number_packed": item.number_packed or 0,
                    "delivery_route_item_name": item.name
                }

                invoices.append(invoice_data)

            except Exception as e:
                frappe.log_error(
                    title="Failed to Get Sales Invoice",
                    message=f"Failed to get invoice {item.invoice_number}: {str(e)}"
                )

        return invoices

    except Exception as e:
        frappe.log_error(
            title="Delivery Route Invoices Fetch Error",
            message=f"Failed to get invoices for delivery route {delivery_route_name}: {str(e)}"
        )
        frappe.throw(f"Failed to get sales invoices: {str(e)}")

@frappe.whitelist()
def update_invoice_workflow_action(invoice_number, action):
    """Update workflow action for a specific sales invoice."""
    try:
        # Get the sales invoice document
        invoice = frappe.get_doc("Sales Invoice", invoice_number)
        # Apply the workflow action
        apply_workflow(invoice, action)
        invoice.reload()

        return {
            "status": "success",
            "message": f"Successfully applied '{action}' to invoice {invoice_number}",
            "new_workflow_state": invoice.workflow_state
        }

    except Exception as e:
        frappe.log_error(
            title="Invoice Workflow Update Error",
            message=f"Failed to update workflow for invoice {invoice_number}: {str(e)}"
        )
        frappe.throw(f"Failed to update invoice workflow: {str(e)}")

def update_invoice_states(doc, method):
    """Sync invoices to route state."""
    if not doc.workflow_state:
        return


    # invoices = doc.get("delivery_route_item") or []
    action= ""
    if doc.workflow_state == "Ready For Delivery":
        action = "Prepare For Delivery"
    elif doc.workflow_state == "Out For Delivery":
        action = "Assign Delivery Route"
    if not action:
        return
    for item in doc.get("delivery_route_item") or []:
        inv = item.invoice_number
        if not inv:
            continue
        invoice = frappe.get_doc("Sales Invoice", inv)
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

@frappe.whitelist()
def return_sales_invoice_to_packed(frm):
    """Return the last sales invoice in the delivery route to 'Packed' state."""
    print("=======frm=========",frm)
    items = frm.doc.delivery_route_item or []
    print("items",items)
    if not items:
        return

    last_item = items[-1]
    if not last_item.invoice_number:
        return

    try:
        invoice = frappe.get_doc("Sales Invoice", last_item.invoice_number)
        if invoice.workflow_state != "Packed":
            apply_workflow(invoice, "Return to Packed")
            invoice.reload()
            frappe.msgprint(f"Invoice {last_item.invoice_number} returned to 'Packed' state.")
    except Exception as e:
        frappe.log_error(
			title="Return Invoice to Packed Error",
			message=f"Failed to return invoice {last_item.invoice_number} to 'Packed': {str(e)}"
		)
        frappe.throw(f"Failed to return invoice to 'Packed': {str(e)}")
