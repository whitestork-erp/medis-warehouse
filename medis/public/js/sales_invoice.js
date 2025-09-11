frappe.ui.form.on('Sales Invoice', {
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
