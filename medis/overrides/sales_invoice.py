import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
import frappe
from frappe import _

from collections import defaultdict
from frappe.model.workflow import apply_workflow


class CustomSalesInvoice(SalesInvoice):

    def on_submit(self):
        if not self._should_split_invoice():
            super().on_submit()
            return

        try:
            self._process_invoice_split()
        except Exception as e:
            frappe.log_error(
                f"Sales Invoice Split Error: {str(e)}", "Sales Invoice Split"
            )
            raise e
        finally:
            frappe.flags._si_split_running = False

    def _process_invoice_split(self):
        """
        Main logic to process the invoice splitting.

        Args:
                doc: Sales Invoice document to split
        """

        # Build groups based on split criteria
        groups = self._build_item_groups()

        if len(groups) == 0:
            frappe.msgprint(_("No splitting required - all items belong to same group"))
            return

        child_invoices = []
        for items in groups.values():
            child_invoice = self._create_child_invoice(items)
            child_invoices.append(child_invoice)

        self._update_parent_references(child_invoices)

    def _build_item_groups(self):
        """
        Group invoice items based on split criteria:
        1. Storage temperature (custom_temperature)
        2. Free medicine flag (free items with Medicine type)

        Returns:
                dict: Groups keyed by (temperature, free_medicine_flag) tuple
        """
        groups = defaultdict(list)


        for item in self.items:
            is_free = bool((item.amount or 0) == 0 or (item.net_amount or 0) == 0)

            custom_med_type = ""
            temperature = None

            try:
                item_doc = frappe.get_cached_doc("Item", item.item_code)
                custom_med_type = item_doc.get("custom_medication_type", "")
                temperature = item_doc.get("custom_storage_type")
            except Exception as e:
                frappe.log_error(
                    f"Error fetching Item {item.item_code}: {str(e)}",
                    "Sales Invoice Split",
                )
                custom_med_type = ""
                temperature = None

            is_medicine = str(custom_med_type).strip() == "Medicine"

            free_medicine_flag = is_free and is_medicine

            group_key = (temperature, free_medicine_flag)

            groups[group_key].append(item)

        return dict(groups)

    def _create_child_invoice(self, items):
        """
        Create a child Sales Invoice for a group of items.

        Args:
                parent_doc: Original Sales Invoice document
                items: List of items for this child invoice
                group_key: Tuple of (currency, temperature, free_medicine_flag)

        Returns:
                Sales Invoice: Created and submitted child invoice
        """
        # currency, temperature, free_medicine_flag = group_key

        # Create new Sales Invoice
        child_doc = frappe.new_doc("Sales Invoice")

        # Copy base header fields from parent
        self._copy_header_fields(child_doc)
        #
        # Set split-specific fields
        child_doc.naming_series = "ACC-SINV-.YYYY.-"
        child_doc.custom_is_split_child = 1
        child_doc.custom_original_invoice = self.name
        child_doc.status = "Unpaid"
        child_doc.workflow_state = "Draft"
        child_doc.update_stock = True
        # Add items to child invoice
        for item in items:
            self._copy_item_to_child(item, child_doc)

        # Copy taxes if they exist
        if self.taxes:
            self._copy_taxes_to_child(child_doc)

        # Insert, save and submit the child invoice
        child_doc.insert(ignore_permissions=True)
        child_doc.save(ignore_permissions=True)
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
        ]

        for field in fields_to_copy:
            if hasattr(self, field) and self.get(field):
                child_doc.set(field, self.get(field))

    def _should_split_invoice(self):
        if not self.naming_series or not self.naming_series.startswith(
            "ACC-VSINV-.YYYY.-"
        ):
            return False

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

            # Save parent document to persist the references
            self.save(ignore_permissions=True)

            # Add system comments linking to child invoices
            comment_links = []
            for child_invoice in child_invoices:
                comment_links.append(
                    f'<a href="/app/sales-invoice/{child_invoice.name}">{child_invoice.name}</a>'
                )

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
                f"Error updating parent references: {str(e)}", "Sales Invoice Split"
            )
            raise e
