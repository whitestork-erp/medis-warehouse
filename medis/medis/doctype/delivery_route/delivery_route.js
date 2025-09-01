frappe.ui.form.on("Delivery Route Item", {
	invoice_number: function (frm) {
		frm.set_query("invoice_number", "delivery_route_item", function (doc, cdt, cdn) {
			let selected_invoices = (doc.delivery_route_item || [])
				.filter((row) => row.name !== cdn)
				.map((row) => row.invoice_number)
				.filter(Boolean);
			return {
				filters: {
					workflow_state: "Packed",
					name: ["not in", selected_invoices],
				},
			};
		});
		frm.refresh_field("delivery_route_item");
	},
	number_packed: function (frm, cdt, cdn) {
		update_summary(frm);
	},
});

frappe.ui.form.on("Delivery Route", {
	onload(frm) {
		frm.set_query("invoice_number", "delivery_route_item", function (doc, cdt, cdn) {
			return {
				filters: {
					workflow_state: "Packed",
				},
			};
		});
	},
	before_workflow_action: async (frm, doc, ac) => {
		console.log("Work Flow Triggered", frm.selected_workflow_action);

		let promise = new Promise((resolve, reject) => {
			frappe.dom.unfreeze();

			if (frm.selected_workflow_action == "Cancel") {
				frappe.confirm(
					"<b>Are you sure you want to cancel this delivery route?</b><br>This will also cancel all associated sales invoices.",
					async () => {
						try {
							// Call backend to cancel all sales invoices for this delivery route
							frappe.call({
								method: "medis.medis.doctype.delivery_route.delivery_route.cancel_delivery_route_invoices",
								args: {
									delivery_route_name: frm.doc.name,
								},
								callback: function (r) {
									if (r.message) {
										frappe.msgprint({
											title: __("Success"),
											message: __(
												"Delivery route and associated sales invoices have been cancelled successfully."
											),
											indicator: "green",
										});
										resolve();
									}
								},
								error: function (r) {
									frappe.msgprint({
										title: __("Error"),
										message: __(
											"Failed to cancel sales invoices. Please try again."
										),
										indicator: "red",
									});
									reject();
								},
							});
						} catch (error) {
							frappe.msgprint({
								title: __("Error"),
								message: __("An unexpected error occurred: ") + error.message,
								indicator: "red",
							});
							reject();
						}
					},
					() => reject()
				);
			} else if (frm.selected_workflow_action == "Deliver") {
				// Show delivery management dialog
				show_delivery_management_dialog(frm, resolve, reject);
			} else {
				resolve();
			}
		});
		await promise.catch(() => frappe.throw());
	},
});

// Calculate summary
function update_summary(frm) {
	const items = frm.doc.delivery_route_item || [];

	frm.set_value("total_invoices", items.length);

	let unique_customers = [...new Set(items.map((r) => r.customer))].length;
	frm.set_value("total_customers", unique_customers);

	let total_packages = items.reduce((sum, r) => sum + (r.number_packed || 0), 0);
	frm.set_value("total_packages", total_packages);
}

// Show delivery management dialog
function show_delivery_management_dialog(frm, resolve, reject) {
	console.log("-----------frm-----------", frm);
	// Get all invoices for this delivery route
	// frappe.call({
	// 	method: "medis.medis.doctype.delivery_route.delivery_route.get_delivery_route_invoices",
	// 	args: {
	// 		delivery_route_name: frm.doc.name
	// 	},
	// 	callback: function(r) {
	// 		if (r.message && r.message.length > 0) {
	// 			let invoices = r.message;

	// 			// Create the dialog
	// 			let dialog = new frappe.ui.Dialog({
	// 				title: __("Manage Invoice Deliveries"),
	// 				size: "large",
	// 				fields: [
	// 					{
	// 						fieldtype: "HTML",
	// 						fieldname: "invoice_list",
	// 						options: generate_invoice_list_html(invoices)
	// 					}
	// 				],
	// 				primary_action_label: __("Apply Actions"),
	// 				primary_action: function() {
	// 					apply_invoice_actions(dialog, invoices, frm, resolve, reject);
	// 				},
	// 				secondary_action_label: __("Cancel"),
	// 				secondary_action: function() {
	// 					dialog.hide();
	// 					reject();
	// 				}
	// 			});

	// 			// Show dialog first
	// 			dialog.show();

	// 			// Add event listeners for action buttons after dialog is shown
	// 			setup_invoice_action_listeners(dialog, invoices);

	// 		} else {
	// 			frappe.msgprint({
	// 				title: __("No Invoices"),
	// 				message: __("No sales invoices found in this delivery route."),
	// 				indicator: "yellow"
	// 			});
	// 			reject();
	// 		}
	// 	},
	// 	error: function(r) {
	// 		frappe.msgprint({
	// 			title: __("Error"),
	// 			message: __("Failed to fetch invoices. Please try again."),
	// 			indicator: "red"
	// 		});
	// 		reject();
	// 	}
	// });

	let invoices = frm.doc.delivery_route_item || [];

	// Create the dialog
	let dialog = new frappe.ui.Dialog({
		title: __("Manage Invoice Deliveries"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "invoice_list",
				options: generate_invoice_list_html(invoices),
			},
		],
		primary_action_label: __("Apply Actions"),
		primary_action: function () {
			apply_invoice_actions(dialog, invoices, frm, resolve, reject);
		},
		secondary_action_label: __("Cancel"),
		secondary_action: function () {
			dialog.hide();
			reject();
		},
	});

	// Show dialog first
	dialog.show();

	// Add event listeners for action buttons after dialog is shown
	setup_invoice_action_listeners(dialog, invoices);
}

// Generate HTML for invoice list
function generate_invoice_list_html(invoices) {
	let html = `
		<div class="invoice-delivery-manager">
			<style>
				.invoice-delivery-manager {
					max-height: 400px;
					overflow-y: auto;
				}
				.invoice-row {
					border: 1px solid #d1d8dd;
					margin-bottom: 10px;
					padding: 15px;
					border-radius: 6px;
					background: #f8f9fa;
				}
				.invoice-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin-bottom: 10px;
				}
				.invoice-info {
					flex: 1;
				}
				.invoice-actions {
					display: flex;
					gap: 8px;
					align-items: center;
				}
				.action-select {
					padding: 6px 12px;
					border: 1px solid #ccc;
					border-radius: 4px;
					cursor: pointer;
					font-size: 12px;
					font-weight: 500;
					background: white;
					color: #333;
					min-width: 100px;
					outline: none;
				}
				.action-select:focus {
					border-color: #17a2b8;
					box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.2);
				}
				.action-label {
					font-size: 12px;
					font-weight: 500;
					color: #495057;
					margin-right: 5px;
				}
				.invoice-details {
					display: grid;
					grid-template-columns: 1fr 1fr 1fr;
					gap: 10px;
					font-size: 13px;
					color: #6c757d;
				}
				.invoice-number {
					font-size: 14px;
					font-weight: 600;
					color: #333;
				}
				.workflow-badge {
					display: inline-block;
					padding: 2px 8px;
					background: #17a2b8;
					color: white;
					border-radius: 12px;
					font-size: 11px;
					font-weight: 500;
					margin-left: 10px;
				}
			</style>
	`;

	invoices.forEach((invoice, index) => {
		html += `
			<div class="invoice-row" data-invoice="${invoice.invoice_number}">
				<div class="invoice-header">
					<div class="invoice-info">
						<span class="invoice-number">${invoice.invoice_number}</span>
					</div>
					<div class="invoice-actions">
						<span class="action-label">Action:</span>
						<select class="action-select" data-invoice="${invoice.invoice_number}">
							<option value="Deliver" selected>Deliver</option>
							<option value="Return">Return</option>
							<option value="Cancel">Cancel</option>
						</select>
					</div>
				</div>
				<div class="invoice-details">
					<div><strong>Customer:</strong> ${invoice.customer_name || invoice.customer}</div>
					<div><strong>Packages:</strong> ${invoice.number_packed || 0}</div>
				</div>
			</div>
		`;
	});

	html += `</div>`;
	return html;
}

// Setup event listeners for action selects
function setup_invoice_action_listeners(dialog, invoices) {
	// Wait for dialog to be fully rendered
	setTimeout(() => {
		// Remove any existing event listeners to prevent duplicates
		dialog.$wrapper.find(".action-select").off("change");

		// Add change event listeners for dropdowns
		dialog.$wrapper.find(".action-select").on("change", function (e) {
			let $select = $(this);
			let invoice_number = $select.attr("data-invoice");
			let action = $select.val();

			console.log("Action changed:", action, "for invoice:", invoice_number);

			// Store the selected action for this invoice
			$select.closest(".invoice-row").attr("data-selected-action", action);

			console.log("Action selected:", action, "for invoice:", invoice_number);
		});

		// Initialize all invoices with default "Deliver" action
		dialog.$wrapper.find(".invoice-row").each(function () {
			$(this).attr("data-selected-action", "Deliver");
		});

		console.log("Event listeners setup complete");
	}, 200);
}

// Apply selected actions to invoices
function apply_invoice_actions(dialog, invoices, frm, resolve, reject) {
	let actions = [];

	// Collect all selected actions
	dialog.$wrapper.find(".invoice-row").each(function () {
		let $row = $(this);
		let invoice_number = $row.data("invoice");
		let selected_action = $row.attr("data-selected-action") || "Deliver";
		console.log("--------", invoice_number, selected_action);
		actions.push({
			invoice_number: invoice_number,
			action: selected_action,
		});
	});


	if (actions.length === 0) {
		frappe.msgprint({
			title: __("No Actions Selected"),
			message: __("Please select actions for the invoices."),
			indicator: "yellow",
		});
		return;
	}

	// Apply actions sequentially
	let completed = 0;
	let failed = 0;

	function apply_next_action(index) {
		if (index >= actions.length) {
			// All actions completed
			dialog.hide();

			let message = `Successfully processed ${completed} invoices.`;
			if (failed > 0) {
				message += ` ${failed} actions failed.`;
			}

			frappe.msgprint({
				title: __("Actions Applied"),
				message: __(message),
				indicator: completed > 0 ? "green" : "red",
			});

			if (completed > 0) {
				resolve();
			} else {
				reject();
			}
			return;
		}

		let action_data = actions[index];

		frappe.call({
			method: "medis.medis.doctype.delivery_route.delivery_route.update_invoice_workflow_action",
			args: {
				invoice_number: action_data.invoice_number,
				action: action_data.action,
			},
			callback: function (r) {
				if (r.message && r.message.status === "success") {
					completed++;
				} else {
					failed++;
				}
				apply_next_action(index + 1);
			},
			error: function (r) {
				failed++;
				apply_next_action(index + 1);
			},
		});
	}

	apply_next_action(0);
}
