app_name = "medis"
app_title = "Medis"
app_publisher = "Marwa"
app_description = "Medis"
app_email = "moussamarwa519@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "medis",
        "logo": "/assets/medis/images/health.webp",
        "title": "Medis",
        "route": "/app/medis-dashboard",
        "has_permission": False,
    }
]

# Includes in <head>
# ------------------

website_context = {
	"favicon": '/assets/medis/images/health.webp',
	"splash_image": "/assets/medis/images/health.webp"
}

# hooks.py in your custom app
# include js, css files in header of desk.html
# app_include_css = "/assets/medis/css/medis.css"
# app_include_js = "assets/medis/js/invoice_status_updater.js"
# app_include_js = ["/assets/medis/js/desktop.js"]
app_include_js = "/assets/medis/js/desktop.js"
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in", ["Sales Invoice-workflow_state"]]],
    },
    {
        "dt": "Role",
        "filters": [["name", "in", ["Delivery Route Manager","Controller","Picker","Sales Manager"]]],
    },
    {
        "dt": "Role Profile",
        "filters": [["name", "in", ["Medis - Delivery Route Manager","Picker Profile","Medis - Controller"]]],
    },
    {
        "dt": "Workflow",
        "filters": [["name", "in", ["Sales Invoice Workflow", "Delivery Route Workflow"]]],
    },
    {
        "dt": "Custom HTML Block",
        "filters": [["name", "in", ["Controller Scanning Screen", "Picker Scanning Screen"]]],
    },
    {
        "dt": "Print Format",
        "filters": [["name", "in", ["Medis Split Invoice"]]],
    },
    "Workflow State",
    "Workflow Action Master",
]


# on_print_pdf = {
#     "Sales Invoice": "medis.utils.increment_print_count"
# }

# fixtures = ["Sales Invoice"]


# include js, css files in header of web template
# web_include_css = "/assets/medis/css/medis.css"
# web_include_js = "/assets/medis/js/medis.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "medis/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Sales Invoice" : "public/js/sales_invoice.js"}
doctype_list_js = {"Sales Invoice": "public/js/sales_invoice_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "medis/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "medis.utils.jinja_methods",
# 	"filters": "medis.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "medis.install.before_install"
# after_install = "medis.medis.scripts.after_install.after_install"

# Uninstallation
# ------------

# before_uninstall = "medis.uninstall.before_uninstall"
# after_uninstall = "medis.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "medis.utils.before_app_install"
# after_app_install = "medis.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "medis.utils.before_app_uninstall"
# after_app_uninstall = "medis.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "medis.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Sales Invoice": "medis.overrides.sales_invoice.CustomSalesInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        "validate": "medis.sales_invoice_item_controller.sales_invoice_validate",
        "before_save": "medis.sales_invoice_item_controller.sales_invoice_before_save",
        "on_update": "medis.sales_invoice_item_controller.sales_invoice_on_update"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"medis.tasks.all"
# 	],
# 	"daily": [
# 		"medis.tasks.daily"
# 	],
# 	"hourly": [
# 		"medis.tasks.hourly"
# 	],
# 	"weekly": [
# 		"medis.tasks.weekly"
# 	],
# 	"monthly": [
# 		"medis.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "medis.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "medis.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "medis.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["medis.utils.before_request"]
# after_request = ["medis.utils.after_request"]


# Job Events
# ----------
# before_job = ["medis.utils.before_job"]
# after_job = ["medis.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"medis.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
