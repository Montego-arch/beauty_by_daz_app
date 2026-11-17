import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Delivery Note": [
				{
					"fieldname": "custom_delivery_status",
					"label": "Delivery Status",
					"fieldtype": "Select",
					"options": "Awaiting Dispatch\nDispatched\nDelivered\nDelivery Failed\nReturned",
					"default": "Awaiting Dispatch",
					"insert_after": "set_posting_time",
					"read_only": 1,
					"module": "Beauty By Daz App",
				},
				{
					"fieldname": "custom_delivered_on",
					"label": "Delivered On",
					"fieldtype": "Datetime",
					"insert_after": "custom_delivery_status",
					"read_only": 1,
					"module": "Beauty By Daz App",
				},
			]
		}
	)
	frappe.db.commit()
