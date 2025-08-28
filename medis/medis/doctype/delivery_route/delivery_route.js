// Copyright (c) 2025, Marwa and contributors
// For license information, please see license.txt
frappe.ui.form.on("Delivery Route Item", {
	invoice_number: function (frm, cdt, cdn) {
		update_summary(frm);

		// const child = locals[cdt][cdn];
		// if (!child.invoice_number) return;

		// --- Fetch Sales Invoice and set fields ---
		// frappe.db.get_doc("Sales Invoice", child.invoice_number)
		//     .then(invoice => {
		//         if (!invoice) {
		//             frappe.msgprint(__('Invoice not found'));
		//             return;
		//         }

		//         frappe.model.set_value(cdt, cdn, "customer", invoice.customer || "");
		//         frappe.model.set_value(cdt, cdn, "territory", invoice.territory || "");
		//         frappe.model.set_value(cdt, cdn, "customer_address", invoice.customer_address || "");

		//         return frappe.db.get_value(
		//             "Invoice Status Updater",
		//             { invoice_number: child.invoice_number },
		//             "number_packed"
		//         );
		//     })
		//     .then(res => {
		//         // if (res) {
		//         //     frappe.model.set_value(cdt, cdn, "number_packed", res.message?.number_packed || "");
		//         // }
		//     })
		//     .catch(err => {
		//         frappe.msgprint(__('Error fetching invoice details: ') + err.message);
		//     });

		// --- Update total_invoices ---
		let total = frm.doc.delivery_route_items.filter((r) => r.invoice_number).length;
		frm.set_value("total_invoices", total);

		// --- Add 2 rows if last row is filled ---
		// let last_row = frm.doc.delivery_route_items[frm.doc.delivery_route_items.length - 1];
		// if (child === last_row && child.invoice_number) {
		//     // let new_row1 = frm.add_child('delivery_route_items');
		//     // let new_row2 = frm.add_child('delivery_route_items');
		//     frm.refresh_field('delivery_route_items');

		//     // Focus handling
		//     setTimeout(() => {
		//         let grid = frm.fields_dict['delivery_route_items'].grid;
		//         let input = grid.wrapper.find(`.grid-row[data-idx="${child.idx}"] [data-fieldname="invoice_number"] input`);
		//         if (input && input.length) {
		//             let e = $.Event('keydown');
		//             e.key = "ArrowDown";
		//             e.which = 40;
		//             input.trigger(e);
		//         }
		//     }, 150);
		// }
	},

	number_packed: function (frm, cdt, cdn) {
		update_summary(frm);
	},

	refresh: function (frm) {
		// Ensure at least 1 row exists
		if (frm.doc.delivery_route_items.length === 0) {
			frm.add_child("delivery_route_items");
			frm.refresh_field("delivery_route_items");
		}

		// Attach focus event listener to first row
		// setTimeout(() => {
		// 	let grid = frm.fields_dict["delivery_route_items"].grid;
		// 	if (grid.grid_rows.length > 0) {
		// 		let first_input = grid.wrapper.find(
		// 			`.grid-row[data-idx="1"] [data-fieldname="invoice_number"] input`
		// 		);
		// 		if (first_input && first_input.length) {
		// 			first_input.off("focus.add_row").on("focus.add_row", function () {
		// 				if (frm.doc.delivery_route_items.length === 1) {
		// 					frm.add_child("delivery_route_items");
		// 					frm.refresh_field("delivery_route_items");
		// 				}
		// 			});
		// 		}
		// 	}
		// }, 300);

		// Focus the first row by default
		// setTimeout(() => {
		//     if (frm.doc.delivery_route_items.length > 0) {
		//         let grid = frm.fields_dict['delivery_route_items'].grid;
		//         grid.grid_rows[0].focus_on_field('invoice_number');
		//     }
		// }, 400);
	},
});

frappe.ui.form.on("Delivery Route", {
	refresh: function (frm) {
		update_summary(frm);

		// frm.fields_dict["delivery_route_items"].grid.get_field("invoice_number").get_query =
		// 	function (doc, cdt, cdn) {
		// 		// collect already selected invoices in child table
		// 		let selected_invoices = (doc.delivery_route_items || []).map(
		// 			(row) => row.invoice_number
		// 		);

		// 		return {
		// 			filters: [
		// 				["Sales Invoice", "workflow_state", "=", "Packed"], // only packed invoices
		// 				["Sales Invoice", "name", "not in", selected_invoices], // exclude already picked
		// 			],
		// 		};
		// 	};

		// if (frm.doc.workflow_state === "Out For Delivery" && !frm.doc.driver) {
		// 	frappe.msgprint({
		// 		title: __("Driver Required"),
		// 		indicator: "red",
		// 		message: __(
		// 			"You must assign a driver before setting this Delivery Route to <b>Out For Delivery</b>."
		// 		),
		// 	});

		// 	// Scroll and focus to driver field
		// 	frm.scroll_to_field("driver");
		// 	frm.set_df_property("driver", "reqd", 1);
		// }
	},
	before_save: function (frm) {
		// Remove empty child rows
		frm.doc.delivery_route_items = frm.doc.delivery_route_items.filter(
			(row) => row.invoice_number
		);
		frm.refresh_field("delivery_route_items");

		// Update total_invoices
		let total = frm.doc.delivery_route_items.length;
		frm.set_value("total_invoices", total);
	},

	delivery_route_items_add: function (frm) {
		update_summary(frm);
	},
	delivery_route_items_remove: function (frm) {
		update_summary(frm);
	},
	delivery_route_items_on_form_rendered: function (frm) {
		update_summary(frm);
	},
});

// frappe.listview_settings["Delivery Route"] = {
// 	onload(listview) {
// 		const currentUserRoles = frappe.boot.user.roles || [];

// 		// Fetch the Delivery Route workflow definition
// 		// frappe.call({
// 		// 	method: "frappe.client.get",
// 		// 	args: {
// 		// 		doctype: "Workflow",
// 		// 		name: "Delivery Route",
// 		// 	},
// 		// 	callback: function (r) {
// 		// 		if (!r.message) return;

// 		// 		const workflow = r.message;
// 		// 		const transitions = workflow.transitions || [];

// 		// 		transitions.forEach((transition) => {
// 		// 			const allowedRoles = transition.allowed || "";
// 		// 			const rolesArray = allowedRoles.split(",").map((role) => role.trim());
// 		// 			const hasAccess = rolesArray.some((role) => currentUserRoles.includes(role));

// 		// 			if (hasAccess) {
// 		// 				listview.page.add_inner_button(transition.action, () => {
// 		// 					const route = frappe.router.slug("Delivery Route Status Updater");
// 		// 					const target_state = encodeURIComponent(transition.next_state);

// 		// 					const new_route = `/app/${route}/new-${frappe.model.scrub(
// 		// 						"Delivery Route Status Updater"
// 		// 					)}-${frappe.utils.get_random(10)}?target_state=${target_state}`;

// 		// 					window.location.href = new_route;
// 		// 				});
// 		// 			}
// 		// 		});
// 		// 	},
// 		// });
// 	},
// };

// calculate summary
function update_summary(frm) {
	const items = frm.doc.delivery_route_items || [];

	frm.set_value("total_invoices", items.length);

	let unique_customers = [...new Set(items.map((r) => r.customer))].length;
	frm.set_value("total_customers", unique_customers);

	let total_packages = items.reduce((sum, r) => sum + (r.number_packed || 0), 0);
	frm.set_value("total_packages", total_packages);
}
