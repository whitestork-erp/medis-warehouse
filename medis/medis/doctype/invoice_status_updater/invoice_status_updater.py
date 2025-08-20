# Copyright (c) 2025, Marwa and contributors
# For license information, please see license.txt

import frappe
from frappe.workflow.doctype.workflow_action.workflow_action import get_next_possible_transitions
from frappe.model.document import Document
import cups
from frappe.utils.jinja import render_template
import jinja2
from frappe import _
import subprocess

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

# @frappe.whitelist()
# def print_packed_invoice(invoice_number, number_packed):
#     # Your print logic here
#     frappe.msgprint(f"Printing invoice {invoice_number} with {number_packed} packages")
@frappe.whitelist()
# def print_packed_invoice(invoice_number, number_packed):
#     print("Printer: Printing invoice", invoice_number, "with", number_packed, "packages")
#     try:
#         number_packed = int(number_packed)

#         # Get the document
#         #doc = frappe.get_doc("Invoice Status Updater", {"invoice_number": invoice_number})
#         doc = frappe.get_doc({
#             "doctype": "Invoice Status Updater",
#             "invoice_number": invoice_number,
#         })
#         print("Document:", doc)

#         # Load print format
#         print_format = frappe.get_doc("Print Format", "Package Label")
#         print("Print Format:", print_format)

#         # Get ZPL template (use fallback if none found)
#         zpl_template = print_format.html
#         if not zpl_template:
#             zpl_template = """
#             ^XA
#             ^FO50,50^A0N,30,30^FDInvoice: {{ doc.invoice_number }}^FS
#             ^FO50,100^A0N,30,30^FDPack: {{ number_packed }}^FS
#             ^XZ
#             """
#         print("ZPL Template:", zpl_template)

#         # Render all labels
#         final_zpl = ""
#         for i in range(1, number_packed + 1):
#             zpl = render_template(
#                 zpl_template,
#                 {"doc": doc, "package_number": f"{i}/{number_packed}"}
#             )
#             final_zpl += zpl

#         # Send ZPL to Zebra printer via CUPS
#         printer_name = "Zebra_GC420t"  # must match lpstat -p output
#         conn = cups.Connection()
#         print("CUPS Connection:", conn)

#         # Save to temp file
#         tmpfile = f"/tmp/{doc.name}.zpl"
#         with open(tmpfile, "w") as f:
#             f.write(final_zpl)   # ✅ use all labels, not just last one

#         # Print raw ZPL
#         conn.printFile(printer_name, tmpfile, f"Invoice {invoice_number} Labels", {"raw": "true"})

#         return f"✅ Printed {number_packed} labels for invoice {invoice_number}"

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Zebra Print Error")
#         return f"❌ Error printing: {str(e)}"
# def print_packed_invoice(invoice_number, number_packed):
#     try:
#         # Get the invoice document to find total packages
#         invoice_doc = frappe.get_doc("Sales Invoice", invoice_number)
        
#         # Extract total packages from custom field or calculate dynamically
#         # Assuming you have a custom field 'total_packages' or similar
#         total_packages = getattr(invoice_doc, 'total_packages', 1)  # Default to 1 if not set
        
#         # Alternative: If you track packages in child table
#         # total_packages = len(invoice_doc.get("packages", [])) or 1
        
#         # Your ZPL template
#         zpl_template = """^XA
# ^FO50,50^A0N,30,30^FDInvoice: {{ invoice_number }}^FS
# ^FO50,100^A0N,30,30^FDPack: {{ pack_number }}/{{ total_packages }}^FS
# ^XZ"""
        
#         # Render the template
#         template = jinja2.Template(zpl_template)
#         rendered_zpl = template.render(
#             invoice_number=invoice_number,
#             pack_number=number_packed,
#             total_packages=total_packages
#         )
        
#         # Get the Network Printer Settings
#         printer_settings_name = frappe.db.get_value("Network Printer Settings", {}, "ZDesignerGC420t")
        
#         if not printer_settings_name:
#             frappe.throw(_("Network Printer Settings not found. Please create it first."))
        
#         printer_settings = frappe.get_doc("Network Printer Settings", printer_settings_name)
        
#         # Set up CUPS connection
#         cups.setServer(printer_settings.server_ip)
#         cups.setPort(printer_settings.port)
#         conn = cups.Connection()
        
#         print(f"Connected to CUPS server at {printer_settings.server_ip}:{printer_settings.port}")
#         # If printer_name is not set, get available printers
#         if not printer_settings.printer_name:
#             printers = conn.getPrinters()
#             if printers:
#                 printer_name = list(printers.keys())[0]
#                 frappe.msgprint(_(f"Using printer: {printer_name}"))
#             else:
#                 frappe.throw(_("No printers found on the server"))
#         else:
#             printer_name = printer_settings.printer_name
        
#         # Print the rendered ZPL
#         job_id = conn.printFile(printer_name, rendered_zpl, "Package Label", {})
        
#         return {
#             "success": True, 
#             "message": f"Package {number_packed} of {total_packages} printed successfully (Job ID: {job_id})",
#             "printer": printer_name
#         }
        
#     except frappe.DoesNotExistError:
#         frappe.throw(_("Network Printer Settings document not found. Please create it first in the UI."))
#     except ImportError:
#         frappe.throw(_("pycups library not installed. Please install it using: pip install pycups"))
#     except cups.IPPError as e:
#         frappe.throw(_(f"Printing error: {str(e)}"))
#     except Exception as e:
#         frappe.log_error(_(f"Printing failed: {str(e)}"))
#         frappe.throw(_("Failed to print package label. Check error log for details."))

def print_packed_invoice(invoice_number, number_packed):
    try:
        # Simple ZPL for testing
        zpl_content = """^XA
^FO50,50^A0N,50,50^FDInvoice: {}^FS
^FO50,120^A0N,50,50^FDPack: {}/2^FS
^XZ""".format(invoice_number, number_packed)
        
        # Create CUPS connection
        conn = cups.Connection()
        
        # Try different approaches
        
        # Method 1: Try using lpr command directly (more reliable)
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.zpl', delete=False) as f:
                f.write(zpl_content)
                temp_file = f.name
            
            # Use lpr command to print
            result = subprocess.run([
                'lpr', 
                '-P', 'ZDesignerGC420t',
                temp_file
            ], capture_output=True, text=True)
            
            # Clean up
            import os
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "✅ Print job sent via lpr command",
                    "method": "lpr_command"
                }
            else:
                frappe.log_error(f"lpr command failed: {result.stderr}")
                
        except Exception as lpr_error:
            frappe.log_error(f"lpr method failed: {lpr_error}")
        
        # Method 2: Try CUPS again with different options
        try:
            job_id = conn.printFile('Zebra_GC420t', zpl_content, "Package Label", {
                'raw': 'true'  # Important for ZPL printers
            })
            return {
                "success": True,
                "message": f"✅ Print job sent via CUPS (Job ID: {job_id})",
                "method": "cups_raw",
                "job_id": job_id
            }
        except cups.IPPError as cups_error:
            frappe.log_error(f"CUPS raw print failed: {cups_error}")
        
        # If both methods fail
        frappe.throw("Failed to print using both methods. Check printer configuration.")
        
    except Exception as e:
        error_msg = f"Printing error: {str(e)}"
        frappe.log_error(error_msg)
        frappe.throw(error_msg)
    try:
        # Simple ZPL code to print "hii"
        zpl_content = """^XA
^FO50,50^A0N,50,50^FDhii^FS
^XZ"""
        
        # Create CUPS connection
        conn = cups.Connection()
        
        # Get all available printers
        printers = conn.getPrinters()
        printers = {name: details for name, details in printers.items() if 'Zebra' in name or 'GC420t' in name}
        print(f"Available printers: {list(printers.keys())}")
        if not printers:
            frappe.throw("❌ No printers found in CUPS. Please configure printers first.")
        
        # Use the first available printer
        printer_name = list(printers.keys())[0]
        print(f"Using printer: {printer_name}")
        # Debug info
        frappe.log_error(f"Printing 'hii' to: {printer_name}")
        frappe.log_error(f"Available printers: {list(printers.keys())}")
        
        # Print the ZPL content
        job_id = conn.printFile(printer_name, zpl_content, "Test Print", {})
        
        return {
            "success": True,
            "message": f"✅ Test print 'hii' sent to '{printer_name}' (Job ID: {job_id})",
            "printer": printer_name,
            "job_id": job_id,
            "available_printers": list(printers.keys())
        }
        
    except cups.IPPError as e:
        error_msg = f"CUPS printing error: {str(e)}"
        frappe.log_error(error_msg)
        frappe.throw(error_msg)
        
    except Exception as e:
        error_msg = f"General printing error: {str(e)}"
        frappe.log_error(error_msg)
        frappe.throw(error_msg)