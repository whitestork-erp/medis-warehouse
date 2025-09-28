import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
import frappe
from frappe import _
from frappe.model.workflow import apply_workflow
from frappe.utils import flt


class CustomSalesInvoice(SalesInvoice):

    def before_submit(self):
        if not self._should_split_invoice():
            super().before_submit()
            return

        try:
            self._process_invoice_split()
            super().before_submit()
        except Exception as e:
            frappe.log_error(
                f"Sales Invoice Split Error: {str(e)}", "Sales Invoice Split"
            )
            raise e

    def on_submit(self):
        # Call parent on_submit first
        self.create_journal_entry()
        super().on_submit()

        # Add comments for split invoices if any
        if hasattr(self, 'custom_split_children') and self.custom_split_children:
            self._add_split_comments()

    def _add_split_comments(self):
        """Add system comments linking to child invoices after successful submission."""
        try:
            comment_links = []
            for split_ref in self.custom_split_children:
                if split_ref.sales_invoice:
                    comment_links.append(
                        f'<a href="/app/sales-invoice/{split_ref.sales_invoice}">{split_ref.sales_invoice}</a>'
                    )

            if comment_links:
                comment_text = _("Invoice split into child invoices: {0}").format(
                    ", ".join(comment_links)
                )

                frappe.get_doc(
                    {
                        "doctype": "Comment",
                        "comment_type": "Info",
                        "reference_doctype": "Sales Invoice",
                        "reference_name": self.name,
                        "content": comment_text,
                    }
                ).insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                f"Error adding split comments: {str(e)}", "Sales Invoice Split"
            )

    def _process_invoice_split(self):
        """
        Main logic to process the invoice splitting.
        Creates separate invoice for free medicine items and removes them from original.
        """

        # Identify free medicine items
        free_medicine_items, regular_items = self._separate_free_medicine_items()

        if not free_medicine_items or not regular_items:
            return
        self._update_parent_quantities(regular_items)

        # Create separate invoice for free medicine items
        child_invoice = self._create_child_invoice(free_medicine_items)

        # Remove free medicine items from current invoice
        self._keep_original_items(regular_items)

        # Update references
        self._update_parent_references([child_invoice])

        # Show alert to user about the split
        self._show_split_alert(child_invoice, len(free_medicine_items))

    def _show_split_alert(self, child_invoice, free_items_count):
        """
        Show user alert about the invoice split.

        Args:
            child_invoice: The created child invoice for free items
            free_items_count: Number of free items moved
        """
        message = _(
            "<b>Invoice Split Alert:</b><br>"
            "{0} free medicine item(s) have been removed from this invoice and moved to a separate invoice.<br><br>"
            "<b>New Invoice ID:</b> <a href='/app/sales-invoice/{1}' target='_blank'>{1}</a><br>"
        ).format(free_items_count, child_invoice.name)

        frappe.msgprint(
            message,
            title=_("Free Items Moved to Separate Invoice"),
            indicator="blue"
        )

    def _separate_free_medicine_items(self):
        """
        Separate free medicine items from regular items.

        Returns:
                tuple: (free_medicine_items, regular_items)
        """
        free_medicine_items = []
        regular_items = []

        for item in self.items:
            is_free = bool((item.amount or 0) == 0 or (item.net_amount or 0) == 0)

            custom_med_type = ""

            try:
                item_doc = frappe.get_cached_doc("Item", item.item_code)
                custom_med_type = item_doc.get("custom_medication_type", "")
            except Exception as e:
                frappe.log_error(
                    f"Error fetching Item {item.item_code}: {str(e)}",
                    "Sales Invoice Split",
                )
                custom_med_type = ""

            is_medicine = str(custom_med_type).strip() == "Medicine"
            is_free_medicine = is_free and is_medicine and item.name

            if is_free_medicine:
                free_medicine_items.append(item)
            elif item.name:
                regular_items.append(item)

        return free_medicine_items, regular_items

    def _keep_original_items(self, regular_items):
        """
        Remove specified items from the original invoice.

        Args:
            items_to_remove: List of items to remove from original invoice
        """
        # # Get the names/indices of items to remove
        # items_to_remove_names = [item.name for item in items_to_remove if item.name]

        # # Filter out the items to be removed
        # remaining_items = []
        # for item in self.items:
        #     if not item.name or item.name not in items_to_remove_names:
        #         remaining_items.append(item)

        # Clear current items and add back only the remaining ones
        self.items = regular_items

    def _update_parent_quantities(self, regular_items):
        count = 0

        for item in regular_items:
            count += item.qty or 0
        self.total_qty = count

    def _create_child_invoice(self, items):
        """
        Create a child Sales Invoice for a group of items.

        Args:
                parent_doc: Original Sales Invoice document
                items: List of items for this child invoice
                group_key: Tuple of (  free_medicine_flag)

        Returns:
                Sales Invoice: Created and submitted child invoice
        """


        # Create new Sales Invoice
        child_doc = frappe.new_doc("Sales Invoice")

        # Copy base header fields from parent
        self._copy_header_fields(child_doc)

        # child_doc.name = f"{self.name}-1"
        # child_doc.flags.name_set = True
        child_doc.custom_is_split_child = 1
        child_doc.custom_original_invoice = self.name
        child_doc.status = "Unpaid"
        child_doc.workflow_state = "Draft"
        child_doc.update_stock = self.update_stock
        # child_doc.run_method("set_missing_values")
        # Add items to child invoice
        for item in items:
            self._copy_item_to_child(item, child_doc)
            child_doc.total_qty = (child_doc.total_qty or 0) + (item.qty or 0)

        # Copy taxes if they exist
        if self.taxes:
            self._copy_taxes_to_child(child_doc)

        if self.sales_team:
            self._copy_sales_team(child_doc)

        # Insert, save and submit the child invoice
        child_doc.insert()
        child_doc.save()
        # child_doc.submit()
        apply_workflow(child_doc,"Submit")

        return child_doc

    def _copy_taxes_to_child(self, child_doc):
        """
        Copy tax entries from parent to child invoice.

        Args:
                parent_doc: Original Sales Invoice
                child_doc: Child Sales Invoice
        """
        if not self.taxes:
            return

        for parent_tax in self.taxes:
            child_tax = child_doc.append("taxes", {})

            tax_fields = [
                "charge_type",
                "account_head",
                "description",
                "included_in_print_rate",
                "included_in_paid_amount",
                "cost_center",
                "rate",
                "account_currency",
                "tax_amount",
                "base_tax_amount",
                "tax_amount_after_discount_amount",
                "base_tax_amount_after_discount_amount",
                "item_wise_tax_detail",
            ]

            for field in tax_fields:
                if hasattr(parent_tax, field):
                    setattr(child_tax, field, getattr(parent_tax, field, None))

    def _copy_item_to_child(self, parent_item, child_doc):
        """
        Copy an item from parent invoice to child invoice.

        Args:
                parent_item: Sales Invoice Item from parent
                child_doc: Child Sales Invoice document
        """
        child_item = child_doc.append("items", {})

        # Copy all relevant item fields
        item_fields = [
            "item_code",
            "item_name",
            "description",
            "item_group",
            "brand",
            "qty",
            "stock_qty",
            "uom",
            "conversion_factor",
            "stock_uom",
            "rate",
            "price_list_rate",
            "base_rate",
            "base_price_list_rate",
            "amount",
            "base_amount",
            "net_rate",
            "base_net_rate",
            "net_amount",
            "base_net_amount",
            "discount_percentage",
            "discount_amount",
            "base_discount_amount",
            "warehouse",
            "income_account",
            "expense_account",
            "cost_center",
            "weight_per_unit",
            "weight_uom",
            "total_weight",
            "batch_no",
            "serial_no",
            "custom_medication_type",
            "custom_storage_type",
        ]

        for field in item_fields:
            if hasattr(parent_item, field):
                setattr(child_item, field, getattr(parent_item, field, None))

    def _copy_header_fields(self, child_doc):
        """
        Copy essential header fields from parent to child invoice.

        Args:
            child_doc: New child Sales Invoice
        """
        fields_to_copy = [
            "company",
            "customer",
            "customer_name",
            "posting_date",
            "posting_time",
            "set_posting_time",
            "due_date",
            "currency",
            "conversion_rate",
            "selling_price_list",
            "price_list_currency",
            "plc_conversion_rate",
            "customer_address",
            "address_display",
            "contact_person",
            "contact_display",
            "contact_mobile",
            "contact_email",
            "shipping_address_name",
            "shipping_address",
            "dispatch_address_name",
            "dispatch_address",
            "company_address",
            "company_address_display",
            "debit_to",
            "project",
            "cost_center",
            "remarks",
            "tc_name",
            "terms",
            "letter_head",
            "select_print_heading",
            "language",
            "customer_group",
            "territory",
            "tax_category",
            "custom_beneficiary",
        ]

        for field in fields_to_copy:
            if hasattr(self, field) and self.get(field):
                child_doc.set(field, self.get(field))

    def _copy_sales_team(self, child_doc):
        """
		Copy sales team entries from parent to child invoice.

		Args:
				parent_doc: Original Sales Invoice
				child_doc: Child Sales Invoice
		"""

        if not self.sales_team:
            return

        for parent_member in self.sales_team:
            child_member = child_doc.append("sales_team", {})

            sales_team_fields = [
				"sales_person",
				"contact_no",
				"allocated_percentage",
				"allocated_amount",
				"commission_rate",
				"incentives"
			]

            for field in sales_team_fields:
                if hasattr(parent_member, field):
                    setattr(child_member, field, getattr(parent_member, field, None))

    def _should_split_invoice(self):

        if self.get("custom_is_split_child"):
            return False

        if not self.items or len(self.items) == 0:
            return False

        return True

    def _update_parent_references(self, child_invoices):
        """
        Update parent invoice with references to created child invoices.

        Args:
                parent_doc: Original Sales Invoice
                child_invoices: List of created child invoices
        """
        try:
            # Clear existing split children if any
            self.custom_split_children = []

            # Add references to each child invoice
            for child_invoice in child_invoices:
                split_ref = self.append("custom_split_children", {})
                split_ref.sales_invoice = child_invoice.name
                split_ref.remarks = _("Auto-split child invoice")

            # Note: Document will be saved automatically during submission process
            # Comments will be added in on_submit after successful submission

        except Exception as e:
            frappe.log_error(
                f"Error updating parent references: {str(e)}", "Sales Invoice Split"
            )
            raise e

    def create_journal_entry(self):
        if not any(item.get("custom_additional_price", 0) != 0 for item in self.items):
            return

        total_additional_price = sum((item.get("custom_additional_price", 0) * item.get("qty", 0)) for item in self.items)
        if not total_additional_price:
            return

        invoice_currency = self.currency
        company_currency = frappe.db.get_value("Company", "MedisPrime", "default_currency")

        account_mapping = {
			"LBP": {
				"receivable": "411000001 - CLIENTS LBP - P",
				"sales": "70100001 - SALES LBP - P",
				"expense": "67510001 - NORMAL OPERATIONS LBP - P"
			},
			"USD": {
				"receivable": "411000002 - CLIENTS USD - P",
				"sales": "70100002 - SALES USD - P",
				"expense": "67510002 - NORMAL OPERATIONS USD - P"
			},
			"EUR": {
				"receivable": "411000003 - CLIENTS EUR - P",
				"sales": "70100003 - SALES EUR - P",
				"expense": "67510003 - NORMAL OPERATIONS EUR - P"
			}
    	}

        if invoice_currency not in account_mapping:
            frappe.throw(
            _("No account mapping configured for currency {0}. Please configure accounts for this currency.").format(invoice_currency)
            )

        accounts = account_mapping[invoice_currency]

        journal_entry_doc = frappe.new_doc("Journal Entry")

        journal_entry_doc.voucher_type = "Journal Entry"
        journal_entry_doc.posting_date = self.posting_date
        journal_entry_doc.company = "MedisPrime"
        journal_entry_doc.user_remark = _("Journal Entry for Sales Invoice {0}").format(self.name)


        if invoice_currency != company_currency:
           journal_entry_doc.multi_currency = 1

        exchange_rate = flt(self.plc_conversion_rate) or 1.0


        cost_center = self.cost_center or get_default_cost_center("MedisPrime")
        # receivable_account = self.debit_to


        abs_amount = abs(flt(total_additional_price))
        company_currency_amount = abs_amount * exchange_rate

        if flt(total_additional_price) > 0:
            journal_entry_doc.append("accounts", {
				"account": accounts["receivable"],
				"debit_in_account_currency": abs(flt(total_additional_price)),
                "credit_in_account_currency": 0,
                "debit": company_currency_amount,  # Company currency amount
            	"credit": 0,
				"party_type": "Customer",
				"party": self.customer,
                # "reference_type": "Sales Invoice",
                # "reference_name": self.name,
                "account_currency": invoice_currency,
                "exchange_rate": exchange_rate,
                "cost_center": cost_center,
            	"user_remark": f"Additional price adjustment - {self.name}"
			})

            journal_entry_doc.append("accounts", {
				"account": accounts["sales"],
                "debit_in_account_currency": 0,
				"credit_in_account_currency": abs(flt(total_additional_price)),
                "debit": 0,
            	"credit": company_currency_amount,
                "account_currency": invoice_currency,
				"exchange_rate": exchange_rate,
				"cost_center": cost_center,
				"user_remark": f"Additional price adjustment - {self.name}"

			})
        else:
            journal_entry_doc.append("accounts", {
				"account": accounts["receivable"],
				"debit_in_account_currency": 0,
				"credit_in_account_currency": abs(flt(total_additional_price)),
				"party_type": "Customer",
				"party": self.customer,
				"reference_type": "Sales Invoice",
				"reference_name": self.name,
				"account_currency": invoice_currency,
				"exchange_rate": exchange_rate,
				"cost_center": cost_center,
				"user_remark": f"Additional price adjustment - {self.name}"
            })
            journal_entry_doc.append("accounts", {
				"account": accounts["expense"],
				"debit_in_account_currency": abs(flt(total_additional_price)),
				"credit_in_account_currency": 0,
				"account_currency": invoice_currency,
				"exchange_rate": exchange_rate,
				"cost_center": cost_center,
				"user_remark": f"Additional price adjustment - {self.name}"
        })
        journal_entry_doc.insert()
        journal_entry_doc.submit()


# def get_default_cost_center():
#     """Get default cost center"""

#     if frappe.db.exists("Selling Settings"):
#         return frappe.db.get_single_value("Selling Settings", "cost_center") or \
#                 frappe.db.get_value("Company", "MedisPrime", "cost_center")


def get_default_cost_center(company):
    """Get default cost center from Company master"""
    # First try to get from Company master
    default_cost_center = frappe.db.get_value("Company", company, "cost_center")

    if default_cost_center:
        return default_cost_center

    # If not set in Company, try to find the main cost center for the company
    cost_centers = frappe.get_all("Cost Center",
        filters={"company": company, "is_group": 0},
        fields=["name"],
        order_by="creation asc",
        limit_page_length=1
    )

    if cost_centers:
        return cost_centers[0].name

    # If still not found, try to find any cost center for the company
    cost_centers = frappe.get_all("Cost Center",
        filters={"company": company},
        fields=["name"],
        limit_page_length=1
    )

    if cost_centers:
        return cost_centers[0].name

    # Last resort - return None and let ERPNext handle it
    return None
