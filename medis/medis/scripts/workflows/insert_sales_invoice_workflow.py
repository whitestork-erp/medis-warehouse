import frappe
import os
import json

def insert_workflow():
    file_path = os.path.join(
        frappe.get_app_path("medis"), "medis", "scripts", "workflows", "sales_invoice_workflow.json"
    )

    with open(file_path, "r") as f:
        workflows = json.load(f)

    for data in workflows:
        workflow_name = data.get("name") or data.get("workflow_name")
        print(f"Processing workflow: {workflow_name}")

        if frappe.db.exists("Workflow", workflow_name):
            print(f"Workflow '{workflow_name}' already exists. Skipping insert.")
            continue

        # Create Workflow States
        states = [state['state'] for state in data.get('states', [])]
        for state in states:
            if not frappe.db.exists("Workflow State", state):
                frappe.get_doc({
                    "doctype": "Workflow State",
                    "workflow_state_name": state
                }).insert(ignore_permissions=True, ignore_mandatory=True)
                print(f"Created Workflow State: {state}")

        # Create Workflow Actions
        actions = [transition['action'] for transition in data.get('transitions', [])]
        for action in actions:
            if not frappe.db.exists("Workflow Action Master", action):
                frappe.get_doc({
                    "doctype": "Workflow Action Master",
                    "workflow_action_name": action
                }).insert(ignore_permissions=True, ignore_mandatory=True)
                print(f"Created Workflow Action: {action}")

        # Insert Workflow
        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()
        print(f"Workflow '{workflow_name}' inserted successfully.")
