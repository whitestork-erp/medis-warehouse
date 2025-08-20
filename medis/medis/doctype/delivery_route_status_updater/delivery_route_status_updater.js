// Copyright (c) 2025, Marwa and contributors
// For license information, please see license.txt

function applyTargetStateFromURL(frm) {
    const urlParams = new URLSearchParams(window.location.search);
    const target = urlParams.get('target_state');
    console.log("🔍 URL target_state:", target);
    if (target && !frm.doc.target_state) {
        frm.set_value('target_state', target);
        console.log("✅ target_state applied to form:", target);
    }
}

function goToNewFormWithSameTarget(targetState) {
    console.log("🔄 Redirecting to new form with target_state:", targetState);
    const newUrl = `/app/delivery-route-status-updater/new?target_state=${encodeURIComponent(targetState)}`;
    window.location.href = newUrl;
}

function prefillDriverIfAvailable(frm) {
    if (frm.doc.delivery_route_number && frm.doc.target_state === "Out For Delivery" && !frm.doc.driver) {
        frappe.db.get_value('Delivery Route', frm.doc.delivery_route_number, 'driver')
            .then(r => {
                if (r.message.driver) {
                    frm.set_value('driver', r.message.driver);
                    console.log("🚗 Prefilled driver:", r.message.driver);
                }
            });
    }
}

frappe.ui.form.on('Delivery Route Status Updater', {
    setup(frm) {
        console.log("✅ Client script loaded!");

        // Enter key handler
        frm._enter_key_handler = function(e) {
            if (e.which === 13 && !$(e.target).is('textarea')) {
                console.log("⏎ Enter key pressed");
                e.preventDefault();
                e.stopPropagation();
                
                // Save form and redirect
                if (frm.doc.target_state) {
                    frm.save(null, function() {
                        goToNewFormWithSameTarget(frm.doc.target_state);
                    });
                }
            }
        };

        $(document).on('keydown', frm._enter_key_handler);
    },

    target_state(frm) {
        // Show/hide driver field
        const showDriver = frm.doc.target_state === "Out For Delivery";
        frm.toggle_reqd("driver", showDriver);
        frm.toggle_display("driver", showDriver);
        frm.refresh_fields();
        
        // Prefill driver if available
        if (showDriver) prefillDriverIfAvailable(frm);
    },

    delivery_route_number(frm) {
        // Prefill driver when route changes
        if (frm.doc.target_state === "Out For Delivery") {
            prefillDriverIfAvailable(frm);
        }
    },

    onload(frm) {
        applyTargetStateFromURL(frm);
        // Initialize driver field visibility
        frm.trigger("target_state");
    },

    refresh(frm) {
        // Add driver field filter
        frm.set_query("driver", function() {
            return {
                filters: {
                    "enabled": 1
                }
            };
        });
    },

    after_save(frm) {
        if (frm.doc.target_state) {
            goToNewFormWithSameTarget(frm.doc.target_state);
        }
    },
   
    onUnload(frm) {
        if (frm._enter_key_handler) {
            $(document).off('keydown', frm._enter_key_handler);
        }
    }
});



