// your_app/public/js/sales_invoice_list.js
frappe.listview_settings['Sales Invoice'] = {
    add_fields: ["workflow_state"],

    onload(listview) {
        // Add custom action column to list view
        this.setup_action_column(listview);
    },

    refresh(listview) {
        // Add print buttons to each row
        this.add_print_buttons(listview);
    },

    setup_action_column(listview) {
        // Add action column header if not already present
        setTimeout(() => {
            const $headerRow = listview.$result.find('.list-row-head');
            if ($headerRow.length && !$headerRow.find('.action-column-header').length) {
                // Find the last visible column and add our action column after it
                const $lastCol = $headerRow.find('.list-row-col').last();
                $lastCol.after(`<div class="list-row-col action-column-header" style="max-width: 100px; min-width: 100px; text-align: center;">
                    <span class="text-muted">Action</span>
                </div>`);
            }
        }, 0);
    },

    add_print_buttons(listview) {
        listview.$result.find('.list-row:not(.list-row-head)').each(function (index) {
            const $row = $(this);

            // Skip if button already exists
            if ($row.find('.btn-print-inline').length) return;

            // Get data from listview.data array
            const rowData = listview.data[index];
            if (!rowData) return;

            const name = rowData.name;
            const state = rowData.workflow_state;

            // Create print button
            const disabled = (state !== 'Pending');
            const $btn = $(`
                <button class="btn btn-xs ${disabled ? 'btn-secondary' : 'btn-primary'} btn-print-inline"
                        ${disabled ? 'disabled' : ''}
                        data-docname="${name}"
                        title="${disabled ? 'Only available for Draft invoices' : 'Print and update workflow'}">
                    Print
                </button>
            `);


			const $lastCol = $row.find('.list-row-col').last();
            const $actionCol = $(`<div class="list-row-col action-column" style="max-width: 100px; min-width: 100px; text-align: center; padding: 8px;"></div>`);
            $actionCol.append($btn);
            $lastCol.after($actionCol);

            // Add click handler
            $btn.on('click', function(e) {
                e.stopPropagation();
                e.preventDefault();

                if (state === 'Pending') {
					console.log("Printing and updating workflow for", name);
                    frappe.call({
                        method: 'frappe.model.workflow.bulk_workflow_approval',
                        args: {
                            doctype: 'Sales Invoice',
                            docnames: [name],
                            action: 'Print'
                        },
                        freeze: true,
                        freeze_message: __('Processing...'),
                        callback(r) {
                            if (!r.exc) {
                                // frappe.show_alert({
                                //     message: __('Sales Invoice printed and workflow updated'),
                                //     indicator: 'green'
                                // });
                                listview.refresh();
                            }
                        }
                    });
                }
            });
        });
    }
};
