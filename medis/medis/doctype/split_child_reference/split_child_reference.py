# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SplitChildReference(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		remarks: DF.Data | None
		sales_invoice: DF.Link

	# end: auto-generated types

	pass
