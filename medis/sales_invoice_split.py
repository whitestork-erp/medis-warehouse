# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowtime, add_to_date, get_time
from collections import defaultdict


def on_submit_split(doc, method):
	"""
	Auto-split Sales Invoice on submit based on specific criteria.

	This function splits a Sales Invoice with naming series ACC-VINV-.YYYY.-
	into multiple child invoices with naming series ACC-SINV-.YYYY.- based on:
	1. Currency grouping
	2. Storage temperature grouping
	3. Free medicine items isolation

	Args:
		doc: Sales Invoice document being submitted
		method: Hook method name (not used)
	"""

	# Guard conditions
	if not _should_split_invoice(doc):
		return

	# Set flag to prevent recursive calls
	if getattr(frappe.flags, '_si_split_running', False):
		return

	frappe.flags._si_split_running = True

	try:
		# Process the split in a transaction for atomicity
		_process_invoice_split(doc)
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Sales Invoice Split Error: {str(e)}", "Sales Invoice Split")
		raise e
	finally:
		frappe.flags._si_split_running = False


def _should_split_invoice(doc):
	"""
	Check if the invoice should be split based on guard conditions.

	Args:
		doc: Sales Invoice document

	Returns:
		bool: True if invoice should be split, False otherwise
	"""
	# Check naming series
	if not doc.naming_series or not doc.naming_series.startswith("ACC-VINV-.YYYY.-"):
		return False

	# Check if it's already a split child (prevent recursion)
	if doc.get("custom_is_split_child"):
		return False

	# Must have items to split
	if not doc.items or len(doc.items) == 0:
		return False

	return True


def _process_invoice_split(doc):
	"""
	Main logic to process the invoice splitting.

	Args:
		doc: Sales Invoice document to split
	"""
	frappe.msgprint(_("Processing invoice split for {0}...").format(doc.name))

	# Build groups based on split criteria
	groups = _build_item_groups(doc)

	# Debug: Log the groups for debugging
	frappe.msgprint(_("Debug: Found {0} groups: {1}").format(len(groups), list(groups.keys())))

	if len(groups) <= 1:
		frappe.msgprint(_("No splitting required - all items belong to same group"))
		return

	# Create child invoices for each group
	child_invoices = []
	for group_key, items in groups.items():
		child_invoice = _create_child_invoice(doc, items, group_key)
		child_invoices.append(child_invoice)

	# Update parent invoice with references to children
	_update_parent_references(doc, child_invoices)

	frappe.msgprint(_("Successfully split invoice {0} into {1} child invoices: {2}").format(
		doc.name, len(child_invoices), ", ".join([inv.name for inv in child_invoices])
	))


def _build_item_groups(doc):
	"""
	Group invoice items based on split criteria:
	1. Currency
	2. Storage temperature (custom_temperature)
	3. Free medicine flag (free items with Medicine type)

	Args:
		doc: Sales Invoice document

	Returns:
		dict: Groups keyed by (currency, temperature, free_medicine_flag) tuple
	"""
	groups = defaultdict(list)

	frappe.msgprint(_("Debug: Starting to group {0} items").format(len(doc.items)))

	for idx, item in enumerate(doc.items):
		# Determine if item is free (amount or net_amount is 0)
		is_free = bool((item.amount or 0) == 0 or (item.net_amount or 0) == 0)

		# Always get custom fields directly from Item master
		custom_med_type = ""
		temperature = None

		try:
			item_doc = frappe.get_cached_doc("Item", item.item_code)
			custom_med_type = item_doc.get("custom_medication_type", "")
			temperature = item_doc.get("custom_temperature")
		except Exception as e:
			frappe.log_error(f"Error fetching Item {item.item_code}: {str(e)}", "Sales Invoice Split")
			# Set defaults if Item cannot be fetched
			custom_med_type = ""
			temperature = None

		# Determine if item is medicine type
		is_medicine = str(custom_med_type).strip() == "Medicine"

		# Free medicine flag - free items that are also medicine type
		free_medicine_flag = is_free and is_medicine

		# Use parent doc currency as default, fall back to item currency if exists
		currency = doc.currency

		# Create grouping key
		group_key = (currency, temperature, free_medicine_flag)

		# Debug information for each item
		frappe.msgprint(_("Debug Item {0} ({1}): amount={2}, custom_temperature='{3}', custom_medication_type='{4}', free={5}, medicine={6}, group_key={7}").format(
			idx + 1,
			item.item_code,
			item.amount,
			temperature,
			custom_med_type,
			is_free,
			is_medicine,
			group_key
		))

		groups[group_key].append(item)

	return dict(groups)


def _create_child_invoice(parent_doc, items, group_key):
	"""
	Create a child Sales Invoice for a group of items.

	Args:
		parent_doc: Original Sales Invoice document
		items: List of items for this child invoice
		group_key: Tuple of (currency, temperature, free_medicine_flag)

	Returns:
		Sales Invoice: Created and submitted child invoice
	"""
	currency, temperature, free_medicine_flag = group_key

	# Create new Sales Invoice
	child_doc = frappe.new_doc("Sales Invoice")

	# Copy base header fields from parent
	_copy_header_fields(parent_doc, child_doc)

	# Set split-specific fields
	child_doc.naming_series = "ACC-SINV-.YYYY.-"
	child_doc.custom_is_split_child = 1
	child_doc.custom_original_invoice = parent_doc.name

	# Add items to child invoice
	for item in items:
		_copy_item_to_child(item, child_doc)

	# Copy taxes if they exist
	if parent_doc.taxes:
		_copy_taxes_to_child(parent_doc, child_doc)

	# Insert, save and submit the child invoice
	child_doc.insert(ignore_permissions=True)
	child_doc.save(ignore_permissions=True)
	child_doc.submit()

	return child_doc


def _copy_header_fields(parent_doc, child_doc):
	"""
	Copy essential header fields from parent to child invoice.

	Args:
		parent_doc: Original Sales Invoice
		child_doc: New child Sales Invoice
	"""
	fields_to_copy = [
		'company', 'customer', 'customer_name', 'posting_date', 'posting_time',
		'set_posting_time', 'due_date', 'currency', 'conversion_rate',
		'selling_price_list', 'price_list_currency', 'plc_conversion_rate',
		'customer_address', 'address_display', 'contact_person', 'contact_display',
		'contact_mobile', 'contact_email', 'shipping_address_name', 'shipping_address',
		'dispatch_address_name', 'dispatch_address', 'company_address',
		'company_address_display', 'debit_to', 'project', 'cost_center',
		'remarks', 'tc_name', 'terms', 'letter_head', 'select_print_heading',
		'language', 'customer_group', 'territory', 'tax_category'
	]

	for field in fields_to_copy:
		if hasattr(parent_doc, field) and parent_doc.get(field):
			child_doc.set(field, parent_doc.get(field))


def _copy_item_to_child(parent_item, child_doc):
	"""
	Copy an item from parent invoice to child invoice.

	Args:
		parent_item: Sales Invoice Item from parent
		child_doc: Child Sales Invoice document
	"""
	child_item = child_doc.append("items", {})

	# Copy all relevant item fields
	item_fields = [
		'item_code', 'item_name', 'description', 'item_group', 'brand',
		'qty', 'stock_qty', 'uom', 'conversion_factor', 'stock_uom',
		'rate', 'price_list_rate', 'base_rate', 'base_price_list_rate',
		'amount', 'base_amount', 'net_rate', 'base_net_rate',
		'net_amount', 'base_net_amount', 'discount_percentage',
		'discount_amount', 'base_discount_amount', 'warehouse',
		'income_account', 'expense_account', 'cost_center', 'weight_per_unit',
		'weight_uom', 'total_weight', 'batch_no', 'serial_no',
		'custom_medication_type', 'custom_temperature'
	]

	for field in item_fields:
		if hasattr(parent_item, field):
			setattr(child_item, field, getattr(parent_item, field, None))


def _copy_taxes_to_child(parent_doc, child_doc):
	"""
	Copy tax entries from parent to child invoice.

	Args:
		parent_doc: Original Sales Invoice
		child_doc: Child Sales Invoice
	"""
	if not parent_doc.taxes:
		return

	for parent_tax in parent_doc.taxes:
		child_tax = child_doc.append("taxes", {})

		tax_fields = [
			'charge_type', 'account_head', 'description', 'included_in_print_rate',
			'included_in_paid_amount', 'cost_center', 'rate', 'account_currency',
			'tax_amount', 'base_tax_amount', 'tax_amount_after_discount_amount',
			'base_tax_amount_after_discount_amount', 'item_wise_tax_detail'
		]

		for field in tax_fields:
			if hasattr(parent_tax, field):
				setattr(child_tax, field, getattr(parent_tax, field, None))


def _update_parent_references(parent_doc, child_invoices):
	"""
	Update parent invoice with references to created child invoices.

	Args:
		parent_doc: Original Sales Invoice
		child_invoices: List of created child invoices
	"""
	try:
		# Clear existing split children if any
		parent_doc.custom_split_children = []

		# Add references to each child invoice
		for child_invoice in child_invoices:
			split_ref = parent_doc.append("custom_split_children", {})
			split_ref.sales_invoice = child_invoice.name
			split_ref.remarks = _("Auto-split child invoice")

		# Save parent document to persist the references
		parent_doc.save(ignore_permissions=True)

		# Add system comments linking to child invoices
		comment_links = []
		for child_invoice in child_invoices:
			comment_links.append(f'<a href="/app/sales-invoice/{child_invoice.name}">{child_invoice.name}</a>')

		comment_text = _("Invoice split into child invoices: {0}").format(", ".join(comment_links))

		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Sales Invoice",
			"reference_name": parent_doc.name,
			"content": comment_text
		}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error updating parent references: {str(e)}", "Sales Invoice Split")
		# Don't fail the entire transaction for reference update issues
		pass
