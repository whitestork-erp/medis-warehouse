# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase


class TestSplitChildReference(FrappeTestCase):
	def test_split_child_reference_creation(self):
		"""Test creation of Split Child Reference doctype"""
		doc = frappe.get_doc({
			"doctype": "Split Child Reference",
			"sales_invoice": "SINV-2025-00001",
			"remarks": "Test child reference"
		})

		# Should not raise an error
		doc.insert()
		self.assertTrue(doc.name)
		self.assertEqual(doc.sales_invoice, "SINV-2025-00001")
		self.assertEqual(doc.remarks, "Test child reference")

		# Clean up
		doc.delete()


if __name__ == '__main__':
	unittest.main()
