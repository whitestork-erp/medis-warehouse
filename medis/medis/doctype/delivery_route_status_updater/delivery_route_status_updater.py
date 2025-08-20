# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.workflow.doctype.workflow_action.workflow_action import get_next_possible_transitions
from frappe.model.document import Document

class DeliveryRouteStatusUpdater(Document):
	pass


@frappe.whitelist()
def update_delivery_route_status(doc, method):
    if hasattr(doc, 'bypass_workflow') and doc.bypass_workflow:
        doc.bypass_workflow = False
        frappe.msgprint(f"⚠️ Delivery Route {doc.delivery_route_number} is already in state '{doc.target_state}'. Skipping transition.")
        return

    route_number = doc.delivery_route_number
    target_state = doc.target_state
    print(f"Updating Delivery Route {route_number} to state '{target_state}'")
    if not route_number or not target_state:
        frappe.throw("❌ Both 'Delivery Route Number' and 'Target State' are required.")

    if not frappe.db.exists("Delivery Route", route_number):
        frappe.throw(f"❌ No Delivery Route found with number {route_number}")

    delivery_route = frappe.get_doc("Delivery Route", route_number)
    current_state = delivery_route.workflow_state
    doc.status = current_state  # Update status field
    print(f"Current state of Delivery Route {route_number}: {current_state}")
    if current_state == target_state:
        frappe.msgprint(f"⚠️ Delivery Route {route_number} is already in state '{target_state}'.")
        return

    workflow_name = frappe.get_value("Workflow", {"document_type": "Delivery Route"}, "name")
    if not workflow_name:
        frappe.throw("❌ No workflow found for 'Delivery Route'")

    transitions = get_next_possible_transitions(workflow_name, current_state, delivery_route)
    valid_transition = next((t for t in transitions if t["next_state"] == target_state), None)
    print(f"Valid transitions from '{current_state}': {[t['next_state'] for t in transitions]}")
    # if not valid_transition:
    #     frappe.throw(f"❌ Invalid transition: Cannot move from '{current_state}' to '{target_state}'")


    # 1️⃣ Update Delivery Route status
    delivery_route.workflow_state = target_state
    delivery_route.save(ignore_permissions=True)
    print(f"✅ Updated Delivery Route {route_number} to '{target_state}'")
    # 2️⃣ Update all invoices in the child table
    for item in delivery_route.get("delivery_route_items"):
        print(f"Processing Delivery Route Item: {item.name}")
        invoice_no = item.invoice_number
        if not invoice_no or not frappe.db.exists("Sales Invoice", invoice_no):
            continue
        print(f"Updating Sales Invoice {invoice_no} to '{target_state}'")
        invoice = frappe.get_doc("Sales Invoice", invoice_no)
        invoice_current_state = invoice.workflow_state
        
        if invoice_current_state != target_state:
            invoice.workflow_state = target_state
            invoice.save(ignore_permissions=True)
            frappe.db.commit()

            frappe.msgprint(f"✅ Updated Sales Invoice {invoice_no} to '{target_state}'")
        else:
            frappe.msgprint(f"⚠️ Sales Invoice {invoice_no} is already in state '{target_state}'")

    frappe.db.commit()

    doc.status = target_state  

def check_driver_before_out(doc, method):
    """
    Prevent setting workflow state to Out For Delivery if no driver assigned.
    """
    if doc.workflow_state == "Out For Delivery" and not doc.driver:
        frappe.throw(
            f"Driver must be assigned for Delivery Route {doc.name}. "
            f"Redirecting you to the form to assign a driver."
        )