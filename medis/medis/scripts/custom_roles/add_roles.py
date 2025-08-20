import frappe
import json
import os

@frappe.whitelist()
def add_roles_from_json():
    # Construct the file path dynamically using frappe.get_app_path
    file_path = os.path.join(
        frappe.get_app_path("medis"), "medis", "scripts", "custom_roles", "custom_roles.json"
    )
    
    # Check if the file exists
    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist."

    # Open and read the JSON file
    with open(file_path, 'r') as f:
        roles_data = json.load(f)
    
    # Track added and skipped roles
    added_roles = []
    skipped_roles = []
    
    # Loop through each role in the JSON data
    for role in roles_data:
        role_name = role.get("role_name")
        description = role.get("description", "No description provided")
        
        # Check if the role already exists in the system
        if not frappe.db.exists("Role", role_name):
            # Create the role
            new_role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "description": description,
                "desk_access": role.get("desk_access"),
                "disabled": role.get("disabled"),
                "is_custom": role.get("is_custom"),
                "restrict_to_domain": role.get("restrict_to_domain"),
                "two_factor_auth": role.get("two_factor_auth")
            })
            new_role.insert(ignore_permissions=True)
            frappe.db.commit()
            added_roles.append(role_name)
            print(f"Role '{role_name}' created successfully.")
        else:
            skipped_roles.append(role_name)
            print(f"Role '{role_name}' already exists, skipping.")
    
    # Return a summary of added and skipped roles
    return {
        "added_roles": added_roles,
        "skipped_roles": skipped_roles
    }
