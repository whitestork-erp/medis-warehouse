function applyTargetStateFromURL(frm) {
    const urlParams = new URLSearchParams(window.location.search);
    const target = urlParams.get('target_state');
    if (target && !frm.doc.target_state) {
        frm.set_value('target_state', target);
    }
}

function goToNewFormWithSameTarget(targetState) {
    frappe.new_doc('Invoice Status Updater');
    setTimeout(() => {
        const baseUrl = window.location.href.split('?')[0];
        const newUrl = `${baseUrl}?target_state=${encodeURIComponent(targetState)}`;
        window.history.replaceState(null, '', newUrl);

        const newForm = frappe.get_cur_form();
        if (newForm && newForm.docname !== frm.docname) {
            newForm.set_value('target_state', targetState);
        }
    }, 300);
}

frappe.ui.form.on('Invoice Status Updater', {
    setup: function(frm) {
        frm._enter_key_handler = async function(e) {
            if (e.which === 13 && !$(e.target).is('data, [type="data"]')) {
                e.preventDefault();
                e.stopPropagation();

                applyTargetStateFromURL(frm);

                const invoiceNumber = frm.doc.invoice_number;
                const targetState = frm.doc.target_state;

                if (!invoiceNumber || !targetState) {
                    frappe.msgprint(__('❌ Both "Invoice Number" and "Target State" are required.'));
                    return;
                }

                const res = await frappe.db.get_value('Sales Invoice', invoiceNumber, ['workflow_state']);
                if (!res || !res.message) {
                    frappe.msgprint(__('❌ Invoice not found.'));
                    return;
                }

                const currentState = res.message.workflow_state;

                if (targetState === "Reviewed") {
                    if (currentState === "Reviewed") {
                        frappe.msgprint(__("❌ Invoice is already Reviewed"));
                        return;
                    }

                    frappe.new_doc('Review Scan', {
                        invoice_number: invoiceNumber
                    });
                    console.log("Redirecting to Review Scan form for invoice:", invoiceNumber);
                    return;
                }

                if (targetState === "Packed") {
                    if (currentState === "Packed") {
                        frappe.msgprint(__("❌ Invoice is already Packed"));
                        return;
                    }

                    let d = new frappe.ui.Dialog({
                        title: __("Enter Number of Packed"),
                        fields: [
                            {
                                label: "Number Of Packed",
                                fieldname: "number_packed",
                                fieldtype: "Int",
                                reqd: 1
                            }
                        ],
                        primary_action_label: __("Print & Save"),
                        primary_action: async (values) => {
                            try {
                                frm.set_value('number_packed', values.number_packed);

                                await frappe.call({
                                    method: "medis.medis.doctype.invoice_status_updater.invoice_status_updater.update_invoice_status_with_packed_number",
                                    args: {
                                        invoice_number: invoiceNumber,
                                        number_packed: values.number_packed,
                                        updater_docname: frm.doc.name
                                    },
                                });

                                frm.set_value('status', 'Packed');
                                await frm.save();

                                await frappe.ui.form.qz_connect();
                                const printers = await frappe.ui.form.qz_get_printer_list();

                                console.log("🖨️ Available Printers from QZ Tray:");
                                printers.forEach((printer, index) => {
                                    console.log(`${index + 1}: ${printer}`);
                                });

                                const printerName = "ZDesigner GC420t"; // Replace with actual printer name
                                if (!printers.includes(printerName)) {
                                    frappe.msgprint(__('❌ Printer not found: ') + printerName);
                                    return;
                                }

                                const config = qz.configs.create(printerName);
                                const zpl = [];

                                for (let i = 1; i <= values.number_packed; i++) {
                                    zpl.push(`^XA
                                    ^FO50,50^A0N,40,40^FDInvoice: ${invoiceNumber}^FS
                                    ^FO50,120^A0N,40,40^FDPackage: ${i}/${values.number_packed}^FS
                                    ^FO50,200^BY2
                                    ^BCN,100,Y,N,N
                                    ^FD${invoiceNumber}^FS
                                    ^XZ`);
                                }

                                await qz.print(config, zpl);
                                frappe.ui.form.qz_success();

                                frappe.msgprint({
                                    message: __('🖨️ Printed invoice {0} with {1} packages', [invoiceNumber, values.number_packed]),
                                    indicator: 'green',
                                    auto_close: true,
                                    alert: 1
                                });

                                goToNewFormWithSameTarget(targetState);
                            } catch (err) {
                                frappe.msgprint(__('❌ Error during save or print: ') + err.message);
                            }
                        }
                    });

                    d.show();
                    return;
                }

                const goToNew = () => goToNewFormWithSameTarget(targetState);

                if (frm.dirty) {
                    frm.save()
                        .then(goToNew)
                        .catch(() => {
                            frappe.msgprint(__('❌ Failed to save. Please try again.'));
                        });
                } else {
                    goToNew();
                }
            }
        };

        $(document).on('keydown', frm._enter_key_handler);
    },

    onload: function(frm) {
        applyTargetStateFromURL(frm);
    },

    after_save: function(frm) {
        if (frm.doc.target_state) {
            goToNewFormWithSameTarget(frm.doc.target_state);
        }
    },

    before_save(frm) {
        if (frm.doc.status === "In Review" && !frm.is_new()) {
            frappe.new_doc("Invoice Review Scan", {
                invoice_number: frm.doc.name
            });
            frappe.throw("Please review and scan items before setting status to Reviewed.");
        }
    },

    onUnload: function(frm) {
        if (frm._enter_key_handler) {
            $(document).off('keydown', frm._enter_key_handler);
        }
    }
});
