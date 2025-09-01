# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.workflow.doctype.workflow_action.workflow_action import apply_workflow

class DeliveryRoute(Document):
	pass

@frappe.whitelist()
def cancel_delivery_route_invoices(delivery_route_name):
    """Cancel all sales invoices associated with the delivery route."""
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

                # Check if invoice is not already cancelled
                if invoice.workflow_state != "Canceled":
                    # Apply cancel workflow action
                    apply_workflow(invoice, "Cancel")
                    invoice.reload()
                    cancelled_invoices.append(item.invoice_number)

            except Exception as e:
                frappe.log_error(
                    title="Failed to Cancel Sales Invoice",
                    message=f"Failed to cancel invoice {item.invoice_number}: {str(e)}"
                )
                failed_invoices.append(item.invoice_number)

        # Prepare response message
        message = f"Successfully cancelled {len(cancelled_invoices)} sales invoices."
        if failed_invoices:
            message += f" Failed to cancel {len(failed_invoices)} invoices: {', '.join(failed_invoices)}"

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
    if doc.workflow_state == "Ready For Delivery1":
        action = "Assign Delivery Route"
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
