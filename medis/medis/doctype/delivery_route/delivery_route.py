import frappe
from frappe.model.document import Document
from frappe.workflow.doctype.workflow_action.workflow_action import apply_workflow
import json

class DeliveryRoute(Document):

	def before_save(self):
		if(self.get("workflow_state") != "Ready For Delivery"): return

		current_items = {row.invoice_number for row in self.delivery_route_item if row.invoice_number}

		try:
			previous_items = set(json.loads(self.get("_last_child_rows") or "[]"))
		except Exception:
			previous_items = set()

		self._last_child_rows = json.dumps(list(current_items))

		linked = current_items - previous_items
		for child_name in linked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Ready For Delivery":
				apply_workflow(child_doc, "Prepare For Delivery")

		unlinked = previous_items - current_items
		for child_name in unlinked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Packed":
				apply_workflow(child_doc, "Repack")

	def on_submit(self):
		submitted_invoices = {row.invoice_number for row in self.delivery_route_item if row.invoice_number}
		for item in submitted_invoices:
			invoice = frappe.get_doc("Sales Invoice", item)
			apply_workflow(invoice, "Assign Delivery Route")

	def validate_workflow(self):
		state = self.get("workflow_state")
		if(state == "Canceled"):
			items = self.get("delivery_route_item") or []
			for item in items:

				invoice = frappe.get_doc("Sales Invoice", item.invoice_number)
				if invoice.workflow_state != "Packed":
					apply_workflow(invoice, "Repack")
					invoice.reload()

		return super().validate_workflow()

# @frappe.whitelist()
# def repack_delivery_route_invoices(delivery_route_name):
#     """Repack all sales invoices associated with the delivery route."""
#     try:
#         delivery_route = frappe.get_doc("Delivery Route", delivery_route_name)

#         items = delivery_route.get("delivery_route_item") or []
#         for item in items:

#             invoice = frappe.get_doc("Sales Invoice", item.invoice_number)
#             if invoice.workflow_state != "Packed":
#                 apply_workflow(invoice, "Repack")
#                 invoice.reload()
#         message = f"Successfully repacked {len(items)} sales invoices."

#         return {
#             "status": "success",
#             "message": message,
#         }

#     except Exception as e:
#         frappe.log_error(
#             title="Delivery Route Invoice Cancellation Error",
#             message=f"Failed to cancel invoices for delivery route {delivery_route_name}: {str(e)}"
#         )
#         frappe.throw(f"Failed to cancel sales invoices: {str(e)}")

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
