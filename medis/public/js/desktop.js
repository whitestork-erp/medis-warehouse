frappe.boot ? add_home_buttons() : frappe.after_ajax(add_home_buttons);

function add_home_buttons() {
    const pages = [
        {
            path: "/app/my-page",                // Invoice Status Updater page
            workflow_name: "Sales Invoice",      // Workflow doctype name
            target_doctype: "Invoice Status Updater"
        }
    ];

    const interval = setInterval(() => {
        const currentPage = pages.find(p => window.location.pathname === p.path);
        if (!currentPage) return;

        const layoutSection = document.querySelector(".codex-editor");
        if (layoutSection && !window.custom_buttons_added) {
            clearInterval(interval);

            const buttonContainer = document.createElement("div");
            buttonContainer.style.marginBottom = "20px";

            const currentUserRoles = frappe.boot.user.roles || [];

            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Workflow",
                    name: currentPage.workflow_name
                },
                callback: function (r) {
                    const workflow = r.message;
                    const transitions = workflow.transitions || [];

                    transitions.forEach((transition) => {
                        const allowedRoles = transition.allowed || "";
                        const rolesArray = allowedRoles.split(',').map(role => role.trim());
                        const hasAccess = rolesArray.some(role => currentUserRoles.includes(role));

                        if (hasAccess) {
                            const button = document.createElement("button");
                            button.className = "btn btn-primary";
                            button.style.marginRight = "10px";
                            button.innerText = transition.action;

                            button.onclick = () => {
                                const route = frappe.router.slug(currentPage.target_doctype);
                                const target_state = encodeURIComponent(transition.next_state);
                                const new_route = `/app/${route}/new-${frappe.model.scrub(currentPage.target_doctype)}-${frappe.utils.get_random(10)}?target_state=${target_state}`;
                                window.location.href = new_route;
                            };

                            buttonContainer.appendChild(button);
                        }
                    });

                    if (buttonContainer.children.length > 0) {
                        layoutSection.prepend(buttonContainer);
                        window.custom_buttons_added = true;
                    } else {
                        console.warn(`[INFO] No workflow actions available for your roles on ${currentPage.workflow_name}.`);
                    }
                }
            });
        }
    }, 300);
}
