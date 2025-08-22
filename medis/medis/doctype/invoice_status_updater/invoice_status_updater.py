# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.workflow.doctype.workflow_action.workflow_action import get_next_possible_transitions
from frappe.model.document import Document
from frappe.utils.jinja import render_template
from frappe import _
import subprocess
import tempfile
import os

class InvoiceStatusUpdater(Document):
    # Add before_save hook to prevent duplicate transitions
    def before_save(self):
        if self.target_state == "Packed" and self.status == "Packed":
            # If already packed, prevent standard transition logic
            self.bypass_workflow = True

@frappe.whitelist()
def update_invoice_status(doc, method):
    # Check if we should bypass workflow (for Packed state)
    if hasattr(doc, 'bypass_workflow') and doc.bypass_workflow:
        doc.bypass_workflow = False  # Reset flag
        return

    invoice_number = doc.invoice_number
    target_state = doc.target_state

    if not invoice_number or not target_state:
        frappe.throw("❌ Both 'Invoice Number' and 'Target State' are required.")

    if not frappe.db.exists("Sales Invoice", invoice_number):
        frappe.throw(f"❌ No Sales Invoice found with number {invoice_number}")

    sales_invoice = frappe.get_doc("Sales Invoice", invoice_number)
    current_state = sales_invoice.workflow_state
    doc.status = current_state  # Update status field

    # Skip if already in target state
    if current_state == target_state:
        return

    workflow_name = frappe.get_value("Workflow", {"document_type": "Sales Invoice"}, "name")
    if not workflow_name:
        frappe.throw("❌ No workflow found for 'Sales Invoice'")

    transitions = get_next_possible_transitions(workflow_name, current_state, sales_invoice)
    valid_transition = next((t for t in transitions if t["next_state"] == target_state), None)

    if not valid_transition:
        frappe.throw(f"❌ Invalid transition: Cannot move from '{current_state}' to '{target_state}'")

    # Update state
    sales_invoice.workflow_state = target_state
    sales_invoice.save(ignore_permissions=True)
    frappe.db.commit()

    doc.status = target_state  # Update status field

@frappe.whitelist()
def update_invoice_status_with_packed_number(invoice_number=None, number_packed=None, updater_docname=None):
    """
    Update invoice to 'Packed' state and save packed number
    """
    if not invoice_number:
        frappe.throw("❌ Invoice number is required")
    if number_packed is None:
        frappe.throw("❌ Number of Packed is required")

    if not frappe.db.exists("Sales Invoice", invoice_number):
        frappe.throw(f"❌ No Sales Invoice found with number {invoice_number}")

    sales_invoice = frappe.get_doc("Sales Invoice", invoice_number)
    current_state = sales_invoice.workflow_state
    target_state = "Packed"

    # Check if already in target state
    if current_state == target_state:
        # Just update the packed number in the updater doc
        if updater_docname and frappe.db.exists("Invoice Status Updater", updater_docname):
            updater_doc = frappe.get_doc("Invoice Status Updater", updater_docname)
            updater_doc.number_packed = number_packed
            updater_doc.status = target_state
            updater_doc.save(ignore_permissions=True)
            frappe.db.commit()
        return True

    workflow_name = frappe.get_value("Workflow", {"document_type": "Sales Invoice"}, "name")
    if not workflow_name:
        frappe.throw("❌ No workflow found for 'Sales Invoice'")

    transitions = get_next_possible_transitions(workflow_name, current_state, sales_invoice)
    valid_transition = next((t for t in transitions if t["next_state"] == target_state), None)

    if not valid_transition:
        frappe.throw(f"❌ Cannot move from '{current_state}' to '{target_state}'")

    # Update invoice state
    sales_invoice.workflow_state = target_state
    sales_invoice.save(ignore_permissions=True)

    # Save packed number to updater doc
    if updater_docname and frappe.db.exists("Invoice Status Updater", updater_docname):
        updater_doc = frappe.get_doc("Invoice Status Updater", updater_docname)
        updater_doc.number_packed = number_packed
        updater_doc.status = target_state  # Update status field

        # Set flag to bypass standard workflow
        updater_doc.bypass_workflow = True
        updater_doc.save(ignore_permissions=True)

    frappe.db.commit()
    return True


