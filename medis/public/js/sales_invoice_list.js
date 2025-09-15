frappe.listview_settings["Sales Invoice"] = {
	add_fields: ["workflow_state"],

	onload(listview) {
		this.setup_action_column(listview);
	},

	refresh(listview) {
		// Add print buttons to each row
		this.add_print_buttons(listview);
	},

	setup_action_column(listview) {
		// Add action column header if not already present
		setTimeout(() => {
			const $headerRow = listview.$result.find(".list-row-head");
			if ($headerRow.length && !$headerRow.find(".action-column-header").length) {
				// Find the last visible column and add our action column after it
				const $lastCol = $headerRow.find(".list-row-col").last();
				$lastCol.after(`<div class="list-row-col action-column-header" style="max-width: 100px; min-width: 100px; text-align: center;">
                    <span class="text-muted">Action</span>
                </div>`);
			}
		}, 0);
	},

	add_print_buttons(listview) {
		listview.$result.find(".list-row:not(.list-row-head)").each(function (index) {
			const $row = $(this);

			if ($row.find(".btn-print-inline").length) return;

			const rowData = listview.data[index];
			if (!rowData) return;

			const name = rowData.name;
			const state = rowData.workflow_state;

			// Create print button
			const disabled = state !== "Pending" || name.startsWith("ACC-VSINV-");

			const $btn = $(`
                <button class="btn btn-xs ${
					disabled ? "btn-secondary" : "btn-primary"
				} btn-print-inline"
                        ${disabled ? "disabled" : ""}
                        data-docname="${name}"
                        title="${
							disabled
								? "Only available for Draft invoices"
								: "Print and update workflow"
						}">
                    Print
                </button>
            `);

			const $lastCol = $row.find(".list-row-col").last();
			const $actionCol = $(
				`<div class="list-row-col action-column" style="max-width: 100px; min-width: 100px; text-align: center; padding: 8px;"></div>`
			);
			$actionCol.append($btn);
			$lastCol.after($actionCol);

			// Add click handler
			$btn.on("click", function (e) {
				e.stopPropagation();
				e.preventDefault();

				if (state === "Pending") {
					console.log("Printing and updating workflow foqqqr", name);
					const frm = frappe.get_doc("Sales Invoice", "ACC-SINV-2025-00013");
					console.log("====================== frm11 =====================", frm);

					// frappe.call({
					// 	method: "silent_print.utils.print_format.print_silently",
					// 	args: {
					// 		doctype: 'Sales Invoice',
					// 		name: 'ACC-SINV-2025-00013',
					// 		print_format: 'Invoice Test',
					// 		print_type: 'Invoice',
					// 	},
					// });

					let printService = new frappe.silent_print.WebSocketPrinter();

					// console.log("--------------------- send2Bridge ------------------");
					frappe.call({
						method: "silent_print.utils.print_format.create_pdf",
						args: {
							doctype: 'Sales Invoice',
							name: 'ACC-SINV-2025-00013',
							silent_print_format: 'Invoice Test',
							no_letterhead: 0,
							_lang: "es",
						},
						callback: (r) => {
							printService.submit({
								type: 'Invoice', //this is the label that identifies the printer in WHB's configuration
								url: "file.pdf",
								file_content: r.message.pdf_base64,
							});
						},
					});

					// send2Bridge(
					// 	frdoc,
					// 	"Invoice Test",
					// 	"HP30138B464FF4(HP Color Laser 150)"
					// );

					// frappe.call({
					//     method: 'frappe.model.workflow.bulk_workflow_approval',
					//     args: {
					//         doctype: 'Sales Invoice',
					//         docnames: [name],
					//         action: 'Print'
					//     },
					//     freeze: true,
					//     freeze_message: __('Processing...'),
					//     callback(r) {
					//         if (!r.exc) {
					//             // frappe.show_alert({
					//             //     message: __('Sales Invoice printed and workflow updated'),
					//             //     indicator: 'green'
					//             // });
					//             send2Bridge(frappe.get_doc("Sales Invoice", name), "Invoice Test", "HP30138B464FF4(HP Color Laser 150)");
					//             listview.refresh();
					//         }
					//     }
					// });
				}
			});
		});
	},
	send2Bridge(frm, print_format, print_type) {
		var printService = new frappe.silent_print.WebSocketPrinter();

		console.log("--------------------- send2Bridge ------------------");
		frappe.call({
			method: "silent_print.utils.print_format.create_pdf",
			args: {
				doctype: frm.doc.doctype,
				name: frm.doc.name,
				silent_print_format: print_format,
				no_letterhead: 1,
				_lang: "es",
			},
			callback: (r) => {
				printService.submit({
					type: print_type, //this is the label that identifies the printer in WHB's configuration
					// url: "file.pdf",
					file_content: r.message.pdf_base64,
				});
			},
		});
	},
	get_indicator: function (doc) {
		// If document is Submitted (docstatus = 1), show the business state
		if (doc.docstatus === 1) {
			let color_map = {
				Unpaid: "orange",
				Overdue: "red",
				"Partly Paid": "yellow",
				Paid: "green",
				Return: "purple",
				"Credit Note Issued": "blue",
			};

			let color = color_map[doc.status] || "blue";
			return [__(doc.status), color, "status,=," + doc.status];
		}

		// For Draft (0) or Cancelled (2), show docstatus value instead
		if (doc.docstatus === 0) {
			return ["Draft", "gray", "docstatus,=,0"];
		}
		if (doc.docstatus === 2) {
			return ["Cancelled", "red", "docstatus,=,2"];
		}

		// fallback if nothing matches
		return [__(doc.status), "blue", "status,=," + doc.status];
	},
};

frappe.provide("frappe.silent_print");
frappe.silent_print.WebSocketPrinter = function (options) {
    console.log("--------------------- WebSocketPrinter ------------------");
    var defaults = {
        url: "ws://127.0.0.1:12212/printer",
        onConnect: function () {
        },
        onDisconnect: function () {
        },
        onUpdate: function () {
        },
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
        if (frappe.whb == undefined){
            frappe.msgprint("Connection to the printer could not be established. Please verify that the  <a href='https://github.com/imTigger/webapp-hardware-bridge' target='_blank'>WebApp Hardware Bridge</a> is running.")
            frappe.whb = true
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
}
