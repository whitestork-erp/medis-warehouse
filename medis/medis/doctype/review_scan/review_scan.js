// Copyright (c) 2025, Marwa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Review Scan', {
    onload(frm) {
        console.log("📥 Review Scan form onload");

        // Initialize scanned items table in memory
        frm.scanned_table_data = [];

        // Load invoice items from backend
        if (frm.doc.invoice_number) {
            frappe.call({
                method: "medis.medis.doctype.review_scan.review_scan.get_old_state_items",
                args: { invoice_number: frm.doc.invoice_number },
                callback: function (r) {
                    if (r.message && r.message.length) {
                        frm.invoice_items = r.message;
                        console.log("📦 Invoice items loaded:", frm.invoice_items);

                        // Initialize scanning after invoice items are loaded
                        initialize_scan_input(frm);
                        render_scanned_items_table(frm);
                    } else {
                        frm.invoice_items = [];
                        frappe.msgprint(__('❌ Invoice items not found for {0}', [frm.doc.invoice_number]));
                    }
                }
            });
        }
    },
     refresh: function(frm) {
        render_scanned_items_table(frm);
    }
});


function initialize_scan_input(frm) {
    console.log("🔍 Initializing scan input for 'Item Number' field...");

    frm.scanned_table_data = frm.scanned_table_data || [];

    const wrapper = frm.fields_dict.item_number?.$wrapper;  // <-- define wrapper
    if (!wrapper || wrapper.length === 0) {
        console.error("❌ 'Item Number' input field not found");
        return;
    }

    // Delegated binding
    wrapper.off("keydown.scan").on("keydown.scan", "input", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            let code = $(this).val().trim();
            $(this).val(""); // clear input

            console.log("📦 Scanned code:", code);

            if (!code) return;

            if (!frm.invoice_items || frm.invoice_items.length === 0) {
                console.error("❌ Invoice items are not loaded yet");
                frappe.msgprint("Invoice items not loaded yet.");
                return;
            }

            let invoiceItem = frm.invoice_items.find(i => i.item_code === code || i.barcode === code);
            console.log("🔍 Matching invoice item:", invoiceItem);

            if (!invoiceItem) {
                frappe.show_alert({ message: `❌ Item ${code} not in invoice`, indicator: 'red' });
                return;
            }

            let existing_row = frm.scanned_table_data.find(r => r.item_code === code);
            if (existing_row) {
                existing_row.qty += 1;
            } else {
                frm.scanned_table_data.push({
                    item_code: invoiceItem.item_code,
                    description: invoiceItem.item_name || "",
                    qty: 1
                });
            }

            console.log("🖥️ Scanned table data:", frm.scanned_table_data);
            render_scanned_items_table(frm);
        }
    });

    console.log("✅ Scan input binding completed");
}


// Render scanned items in HTML table
function render_scanned_items_table(frm) {
    const htmlWrapper = frm.fields_dict['items_html']?.$wrapper;
    if (!htmlWrapper) {
        console.error("❌ HTML field 'items_html' not found for rendering scanned items.");
        return;
    }

    let html = `
        <table class="table table-bordered table-striped">
            <thead>
                <tr>
                    <th>Item Code</th>
                    <th>Description</th>
                    <th>Quantity</th>
                </tr>
            </thead>
            <tbody>
    `;

    frm.scanned_table_data.forEach(row => {
        html += `
            <tr>
                <td>${row.item_code}</td>
                <td>${row.qty}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    htmlWrapper.html(html);
    console.log("🖥️ Rendered scanned items table:", frm.scanned_table_data);
}

