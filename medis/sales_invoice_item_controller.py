import frappe
from frappe import _

def validate_sales_invoice_item(doc, method):
    """
    Server-side validation and processing for Sales Invoice Items with is_free functionality
    """
    for item in doc.items:
        handle_is_free_logic(item, doc)

def handle_is_free_logic(item, parent_doc):
    """
    Handle the is_free logic for individual Sales Invoice Item
    """
    # If is_free is checked, set discount to 100% and bypass pricing rules
    if getattr(item, 'is_free', 0):
        item.discount_percentage = 100
        item.margin_rate_or_amount = 0

        # Clear pricing rules to bypass them
        item.pricing_rules = "[]"

        # Recalculate amounts based on 100% discount
        if item.rate and item.qty:
            item.amount = 0
            item.net_amount = 0
            item.base_amount = 0
            item.base_net_amount = 0

    # Auto-check is_free if discount is 100% or amount is 0
    elif item.discount_percentage == 100 or item.amount == 0:
        if not getattr(item, 'is_free', 0):
            item.is_free = 1
            # Clear pricing rules when auto-setting is_free
            item.pricing_rules = "[]"

    # If is_free is unchecked but was previously set, reset discount
    elif hasattr(item, 'is_free') and not item.is_free and item.discount_percentage == 100:
        # Reset discount only if it was 100% (indicating it was set by is_free)
        item.discount_percentage = 0

def before_save_sales_invoice_item(doc, method):
    """
    Process is_free logic before saving the Sales Invoice
    """
    validate_sales_invoice_item(doc, method)

def on_update_sales_invoice_item(doc, method):
    """
    Process is_free logic after updating the Sales Invoice
    """
    # Additional processing if needed after save
    pass

def validate_pricing_rule_bypass(doc, method):
    """
    Validate that pricing rules are properly bypassed for free items
    """
    for item in doc.items:
        if getattr(item, 'is_free', 0):
            # Ensure no pricing rules are applied to free items
            if item.pricing_rules and item.pricing_rules != "[]":
                frappe.msgprint(
                    _("Pricing rules have been cleared for free item: {0}").format(item.item_code),
                    alert=True
                )
                item.pricing_rules = "[]"

# -------------------- Hook Functions --------------------
def sales_invoice_validate(doc, method):
    """Main validation function to be called from hooks.py"""
    validate_sales_invoice_item(doc, method)
    validate_pricing_rule_bypass(doc, method)

def sales_invoice_before_save(doc, method):
    """Before save function to be called from hooks.py"""
    before_save_sales_invoice_item(doc, method)

def sales_invoice_on_update(doc, method):
    """On update function to be called from hooks.py"""
    on_update_sales_invoice_item(doc, method)
