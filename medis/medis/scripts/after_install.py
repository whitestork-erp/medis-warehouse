def after_install():
    from medis.medis.scripts.workflows.insert_sales_invoice_workflow import insert_workflow
    from medis.medis.scripts.custom_field.import_custom_field import insert_custom_field_from_file
    from medis.medis.scripts.custom_roles.add_roles import add_roles_from_json
    
    add_roles_from_json()
    insert_custom_field_from_file()
    insert_workflow()
    