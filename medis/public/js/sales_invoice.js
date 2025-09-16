// Custom script for Sales Invoice with is_free functionality for Sales Invoice Items

// Global event listener for workflow state changes
$(document).on("app_ready", function () {
	frappe.event_hub.on("sales_invoice_workflow_changed", function (data) {
		console.log("Global handler: Sales Invoice workflow changed", data);

		// Perform global actions based on workflow state
		if (data.workflow_state === "Printed" && frappe.silent_print) {
			// Example: Show a notification
			frappe.show_alert(
				{
					message: __("Invoice {0} has been printed", [data.name]),
					indicator: "green",
				},
				5
			);
		}
	});
});

frappe.ui.form.on("Sales Invoice", {
	setup: function (frm) {
		// Initialize the form setup

		// Store the original workflow state to compare after changes
		frm.workflow_state_before_action = frm.doc.workflow_state;
	},


	after_workflow_action: function (frm) {
		console.log("After workflow action:", frm.doc.workflow_state);
		if (frm.doc.workflow_state == "Ready For Picking") {
			let printService = new frappe.silent_print.WebSocketPrinter();
			frappe.call({
				method: "silent_print.utils.print_format.create_pdf",
				args: {
					doctype: "Sales Invoice",
					name: frm.doc.name,
					silent_print_format: "Medis Split Invoice",
					no_letterhead: 0,
					_lang: "en",
				},
				callback: (r) => {
					printService.submit({
						type: "Invoice Printer",
						url: "file.pdf",
						file_content: r.message.pdf_base64,
					});
				},
			});
		}
	},

	refresh: function (frm) {
		// Auto-check is_free for items with 100% discount or zero amount
		frm.doc.items.forEach(function (item, index) {
			if (item.discount_percentage == 100 || item.amount == 0) {
				if (!item.is_free) {
					frappe.model.set_value(item.doctype, item.name, "is_free", 1);
				}
			}
		});
	},
	naming_series(frm) {
		if (!frm.doc.naming_series) return;

		const hide_it = frm.doc.naming_series.startsWith("ACC-VSINV-");
		frm.toggle_display("update_stock", !hide_it); // hide when ACC-VSINV-
		if (hide_it) {
			frm.set_value("update_stock", 0);
		}
	},

	onload(frm) {
		frm.trigger("naming_series");
	},
	// workflow_state(frm) {
	// 	console.log("workflow_state changed to:", frm.doc.workflow_state);

	// 	// Handle different workflow states
	// 	switch(frm.doc.workflow_state) {
	// 		case "Pending":
	// 			console.log("Invoice is now Pending");
	// 			break;

	// 		case "Printed":
	// 			console.log("Invoice is now Printed");
	// 			break;

	// 		case "Paid":
	// 			console.log("Invoice is now Paid");
	// 			break;

	// 		case "Cancelled":
	// 			console.log("Invoice is now Cancelled");
	// 			break;

	// 		default:
	// 			// Default handling for other states
	// 			break;
	// 	}

	// 	// Example of updating UI based on workflow state
	// 	// const isEditable = ["Draft", "Pending"].includes(frm.doc.workflow_state);
	// 	// frm.toggle_enable('items', isEditable);
	// 	// frm.toggle_enable('payment_terms_template', isEditable);

	// 	// // Trigger custom event that other modules can listen to
	// 	// frappe.event_hub.trigger('sales_invoice_workflow_changed', {
	// 	// 	name: frm.doc.name,
	// 	// 	workflow_state: frm.doc.workflow_state,
	// 	// 	doctype: frm.doc.doctype
	// 	// });
	// }
});

frappe.ui.form.on("Sales Invoice Item", {
	is_free: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		if (item.is_free) {
			// When is_free is checked, set discount to 100% and bypass pricing rules
			frappe.model.set_value(cdt, cdn, "discount_percentage", 100);
			frappe.model.set_value(cdt, cdn, "margin_rate_or_amount", 0);

			// Clear pricing rule reference to bypass it
			if (item.pricing_rules) {
				frappe.model.set_value(cdt, cdn, "pricing_rules", "[]");
			}

			// Recalculate amounts
			frm.script_manager.trigger("discount_percentage", cdt, cdn);
		} else {
			// When is_free is unchecked, reset discount and re-apply pricing rules
			frappe.model.set_value(cdt, cdn, "discount_percentage", 0);

			// Trigger pricing rule re-application
			frm.script_manager.trigger("item_code", cdt, cdn);
		}
	},

	discount_percentage: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// Auto-check is_free when discount is 100%
		if (item.discount_percentage == 100 && !item.is_free) {
			frappe.model.set_value(cdt, cdn, "is_free", 1);
		} else if (item.discount_percentage != 100 && item.is_free && !frm._setting_is_free) {
			// Uncheck is_free if discount is changed from 100% (but not when we're setting it programmatically)
			frappe.model.set_value(cdt, cdn, "is_free", 0);
		}
	},

	amount: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// Auto-check is_free when amount is 0
		if (item.amount == 0 && !item.is_free) {
			frappe.model.set_value(cdt, cdn, "is_free", 1);
		} else if (item.amount != 0 && item.is_free && !frm._setting_is_free) {
			// Uncheck is_free if amount is changed from 0 (but not when we're setting it programmatically)
			frappe.model.set_value(cdt, cdn, "is_free", 0);
		}
	},

	rate: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// When rate changes and item is marked as free, maintain 100% discount
		if (item.is_free) {
			frm._setting_is_free = true;
			frappe.model.set_value(cdt, cdn, "discount_percentage", 100);
			setTimeout(() => {
				frm._setting_is_free = false;
			}, 100);
		}
	},

	qty: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// When quantity changes and item is marked as free, maintain 100% discount
		if (item.is_free) {
			frm._setting_is_free = true;
			frappe.model.set_value(cdt, cdn, "discount_percentage", 100);
			setTimeout(() => {
				frm._setting_is_free = false;
			}, 100);
		}
	},

	item_code: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// If item is marked as free, prevent pricing rule application and set discount to 100%
		if (item.is_free) {
			setTimeout(() => {
				frm._setting_is_free = true;
				frappe.model.set_value(cdt, cdn, "discount_percentage", 100);
				if (item.pricing_rules) {
					frappe.model.set_value(cdt, cdn, "pricing_rules", "[]");
				}
				setTimeout(() => {
					frm._setting_is_free = false;
				}, 100);
			}, 500); // Delay to allow pricing rules to be applied first, then override
		}
	},
});

frappe.provide("frappe.silent_print");
frappe.silent_print.WebSocketPrinter = function (options) {
	var defaults = {
		url: "ws://127.0.0.1:12212/printer",
		onConnect: function () {},
		onDisconnect: function () {},
		onUpdate: function () {},
	};

	var settings = Object.assign({}, defaults, options);
	var websocket;
	var connected = false;

	var onMessage = function (evt) {
		settings.onUpdate(evt.data);
	};

	var onConnect = function () {
		connected = true;
		settings.onConnect();
	};

	var onDisconnect = function () {
		connected = false;
		settings.onDisconnect();
		reconnect();
	};

	var onError = function () {
		if (frappe.whb == undefined) {
			frappe.msgprint(
				"No se pudo establecer conexión con la impresora. Favor verificar que el <a href='https://github.com/imTigger/webapp-hardware-bridge' target='_blank'>WebApp Hardware Bridge</a> esté ejecutándose."
			);
			frappe.whb = true;
		}
	};

	var connect = function () {
		websocket = new WebSocket(settings.url);
		websocket.onopen = onConnect;
		websocket.onclose = onDisconnect;
		websocket.onmessage = onMessage;
		websocket.onerror = onError;
	};

	var reconnect = function () {
		connect();
	};

	this.submit = function (data) {
		console.log("Submitting to printer ===========1");
		if (Array.isArray(data)) {
			data.forEach(function (element) {
				websocket.send(JSON.stringify(element));
			});
		} else {
			websocket.send(JSON.stringify(data));
		}
	};

	this.isConnected = function () {
		return connected;
	};

	connect();
};
