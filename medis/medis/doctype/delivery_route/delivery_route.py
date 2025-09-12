import frappe
from frappe.model.document import Document
from frappe.workflow.doctype.workflow_action.workflow_action import apply_workflow
import json
from frappe.model.workflow import bulk_workflow_approval

class DeliveryRoute(Document):

	def before_save(self):
		if(self.get("workflow_state") != "Ready For Delivery"): return

		current_items = {row.invoice_number for row in self.delivery_route_item if row.invoice_number}

		try:
			previous_items = set(json.loads(self.get("_last_child_rows") or "[]"))
		except Exception:
			previous_items = set()

		self._last_child_rows = json.dumps(list(current_items))

		added_children_docs = []
		linked = current_items - previous_items
		for child_name in linked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Ready For Delivery":
				added_children_docs.append(child_doc)
		if added_children_docs:
			bulk_workflow_approval(json.dumps([doc.name for doc in added_children_docs]),"Sales Invoice","Prepare For Delivery")

		removed_children_docs = []
		unlinked = previous_items - current_items
		for child_name in unlinked:
			child_doc = frappe.get_doc("Sales Invoice", child_name)
			if child_doc.workflow_state != "Packed":
				removed_children_docs.append(child_doc)

		if removed_children_docs:
			bulk_workflow_approval(json.dumps([doc.name for doc in removed_children_docs]),"Sales Invoice","Repack")

	def on_submit(self):
		submitted_invoices = {row.invoice_number for row in self.delivery_route_item if row.invoice_number}
		submitted_invoices_docs = []
		for item in submitted_invoices:
			invoice = frappe.get_doc("Sales Invoice", item)
			submitted_invoices_docs.append(invoice)
		bulk_workflow_approval(json.dumps([doc.name for doc in submitted_invoices_docs]),"Sales Invoice","Assign Delivery Route")

@frappe.whitelist()
def repack_delivery_route_invoices(delivery_route_name):
    """Repack all sales invoices associated with the delivery route."""
    try:
        delivery_route = frappe.get_doc("Delivery Route", delivery_route_name)

        cancelled_invoices = []
        failed_invoices = []

        cancelled_invoices_docs = []
        for item in delivery_route.get("delivery_route_item") or []:

            try:
                invoice = frappe.get_doc("Sales Invoice", item.invoice_number)

                if invoice.workflow_state != "Packed":
                    cancelled_invoices_docs.append(invoice)
                    cancelled_invoices.append(item.invoice_number)

            except Exception as e:
                frappe.log_error(
                    title="Failed to Repack Sales Invoice",
                    message=f"Failed to repack invoice {item.invoice_number}: {str(e)}"
                )
                failed_invoices.append(item.invoice_number)

        if cancelled_invoices_docs:
            bulk_workflow_approval(json.dumps([doc.name for doc in cancelled_invoices_docs]), "Sales Invoice", "Repack")

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
