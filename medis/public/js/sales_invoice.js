// Custom script for Sales Invoice with is_free functionality for Sales Invoice Items

frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        // Initialize the form setup
    },

    refresh: function(frm) {
        // Auto-check is_free for items with 100% discount or zero amount
        frm.doc.items.forEach(function(item, index) {
            if (item.discount_percentage == 100 || item.amount == 0) {
                if (!item.is_free) {
                    frappe.model.set_value(item.doctype, item.name, 'is_free', 1);
                }
            }
        });
    },
	naming_series(frm) {
        if (!frm.doc.naming_series) return;

        const hide_it = frm.doc.naming_series.startsWith('ACC-VSINV-');
        frm.toggle_display('update_stock', !hide_it);   // hide when ACC-VSINV-
        if (hide_it) {
            frm.set_value('update_stock', 0);
        }
    },

    onload(frm) {
        frm.trigger('naming_series');
	}
});

frappe.ui.form.on('Sales Invoice Item', {
    is_free: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        if (item.is_free) {
            // When is_free is checked, set discount to 100% and bypass pricing rules
            frappe.model.set_value(cdt, cdn, 'discount_percentage', 100);
            frappe.model.set_value(cdt, cdn, 'margin_rate_or_amount', 0);

            // Clear pricing rule reference to bypass it
            if (item.pricing_rules) {
                frappe.model.set_value(cdt, cdn, 'pricing_rules', '[]');
            }

            // Recalculate amounts
            frm.script_manager.trigger('discount_percentage', cdt, cdn);
        } else {
            // When is_free is unchecked, reset discount and re-apply pricing rules
            frappe.model.set_value(cdt, cdn, 'discount_percentage', 0);

            // Trigger pricing rule re-application
            frm.script_manager.trigger('item_code', cdt, cdn);
        }
    },

    discount_percentage: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        // Auto-check is_free when discount is 100%
        if (item.discount_percentage == 100 && !item.is_free) {
            frappe.model.set_value(cdt, cdn, 'is_free', 1);
        } else if (item.discount_percentage != 100 && item.is_free && !frm._setting_is_free) {
            // Uncheck is_free if discount is changed from 100% (but not when we're setting it programmatically)
            frappe.model.set_value(cdt, cdn, 'is_free', 0);
        }
    },

    amount: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        // Auto-check is_free when amount is 0
        if (item.amount == 0 && !item.is_free) {
            frappe.model.set_value(cdt, cdn, 'is_free', 1);
        } else if (item.amount != 0 && item.is_free && !frm._setting_is_free) {
            // Uncheck is_free if amount is changed from 0 (but not when we're setting it programmatically)
            frappe.model.set_value(cdt, cdn, 'is_free', 0);
        }
    },

    rate: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        // When rate changes and item is marked as free, maintain 100% discount
        if (item.is_free) {
            frm._setting_is_free = true;
            frappe.model.set_value(cdt, cdn, 'discount_percentage', 100);
            setTimeout(() => {
                frm._setting_is_free = false;
            }, 100);
        }
    },

    qty: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        // When quantity changes and item is marked as free, maintain 100% discount
        if (item.is_free) {
            frm._setting_is_free = true;
            frappe.model.set_value(cdt, cdn, 'discount_percentage', 100);
            setTimeout(() => {
                frm._setting_is_free = false;
            }, 100);
        }
    },

    item_code: function(frm, cdt, cdn) {
        let item = locals[cdt][cdn];

        // If item is marked as free, prevent pricing rule application and set discount to 100%
        if (item.is_free) {
            setTimeout(() => {
                frm._setting_is_free = true;
                frappe.model.set_value(cdt, cdn, 'discount_percentage', 100);
                if (item.pricing_rules) {
                    frappe.model.set_value(cdt, cdn, 'pricing_rules', '[]');
                }
                setTimeout(() => {
                    frm._setting_is_free = false;
                }, 100);
            }, 500); // Delay to allow pricing rules to be applied first, then override
        }
    }
});
