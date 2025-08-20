import frappe
import os
import json

def insert_custom_field_from_file():
    file_path = os.path.join(
        frappe.get_app_path("medis"), "medis",
        "scripts",
        "custom_field",
        "custom_field.json"
    )

    # Load JSON file
    with open(file_path, "r") as f:
        fields = json.load(f)

    for field_data in fields:
        # Compose the unique name of the Custom Field
        field_name = f"{field_data['dt']}-{field_data['fieldname']}"

        # Check if already exists
        if frappe.db.exists("Custom Field", field_name):
            print(f"Custom Field '{field_name}' already exists, skipping.")
            continue

        # Create and insert the Custom Field document
        doc = frappe.get_doc(field_data)
        doc.insert()
        print(f"Inserted Custom Field '{field_name}' successfully.")

    frappe.db.commit()
