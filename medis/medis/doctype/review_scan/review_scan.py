# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReviewScan(Document):
	pass

@frappe.whitelist()
def get_old_state_items(invoice_number):
    """
    Fetch items from the given invoice for comparison.
    """
    return frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": invoice_number},
        fields=["item_code", "qty"]
    )

@frappe.whitelist()
def set_invoice_reviewed(invoice_number):
    """
    Move Sales Invoice to Reviewed state.
    """
    inv = frappe.get_doc("Sales Invoice", invoice_number)
    inv.workflow_state = "Reviewed"
    inv.save(ignore_permissions=True)
    frappe.db.commit()
    return True
