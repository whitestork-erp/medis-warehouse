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
		setTimeout(() => {
			const $headerRow = listview.$result.find(".list-row-head");
			if ($headerRow.length && !$headerRow.find(".action-column-header").length) {
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

			$btn.on("click", async function (e) {
				e.stopPropagation();
				e.preventDefault();

				const doc = await frappe.db.get_doc("Sales Invoice", name);

				if (state === "Pending") {
					console.log("Printing and updating workflow for", name);
					let printService = new frappe.silent_print.WebSocketPrinter();

					frappe.call({
                        method: 'frappe.model.workflow.apply_workflow',
                        args: {
                            doc,
                            action: 'Print'
                        },
                        freeze: true,
                        freeze_message: __('Processing...'),
                        callback(r) {
                            listview.refresh();
                        }
                    });

					frappe.call({
						method: "silent_print.utils.print_format.create_pdf",
						args: {
							doctype: 'Sales Invoice',
							name: name,
							silent_print_format: 'Medis Split Invoice',
							no_letterhead: 0,
							_lang: "en",
						},
						callback: (r) => {
							printService.submit({
								type: 'Invoice Printer',
								url: "file.pdf",
								file_content: r.message.pdf_base64,
							});
						},
					});
				}
			});
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
            frappe.msgprint("Could not connect to the printer. Please verify that the <a href='https://github.com/imTigger/webapp-hardware-bridge' target='_blank'>WebApp Hardware Bridge</a> is running.")
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
}
