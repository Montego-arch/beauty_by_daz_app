import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

# Must match the "custom_delivery_status" Select options on Delivery Note.
STATUSES = ["Awaiting Dispatch", "Dispatched", "Delivered", "Delivery Failed", "Returned"]
STATUS_BY_LOWER = {s.lower(): s for s in STATUSES}


@frappe.whitelist()
def update_delivery_status(delivery_note, status, delivered_on=None):
	"""Called by ShipBubble when a shipment's status changes.

	Sets the Delivery Note's delivery status to match. "Delivered" also
	submits the Delivery Note if it's still a draft. An unrecognised status
	is acknowledged but ignored, so ShipBubble can call this on every status
	change without needing to know exactly which values we accept.
	"""
	if not frappe.db.exists("Delivery Note", delivery_note):
		frappe.throw(
			_("Delivery Note {0} not found").format(delivery_note),
			frappe.DoesNotExistError,
		)

	frappe.has_permission("Delivery Note", "write", doc=delivery_note, throw=True)

	canonical_status = STATUS_BY_LOWER.get((status or "").strip().lower())
	if not canonical_status:
		return {
			"delivery_note": delivery_note,
			"ignored": True,
			"reason": f"status {status!r} is not handled",
		}

	doc = frappe.get_doc("Delivery Note", delivery_note)

	if doc.docstatus == 2:
		frappe.throw(_("Delivery Note {0} is cancelled and cannot be updated").format(delivery_note))

	if canonical_status != "Delivered":
		if doc.docstatus == 1 and canonical_status != "Returned":
			# Once submitted (i.e. already Delivered), only a later Return is a
			# legitimate forward move. Anything else is a late or out-of-order
			# webhook call and would otherwise silently undo the delivery.
			return {
				"delivery_note": doc.name,
				"ignored": True,
				"reason": f"Delivery Note is already submitted, cannot move back to {canonical_status!r}",
			}
		doc.db_set("custom_delivery_status", canonical_status)
		return {"delivery_note": doc.name, "status": canonical_status, "docstatus": doc.docstatus}

	if doc.docstatus == 1 and doc.custom_delivery_status == "Delivered":
		return {
			"delivery_note": doc.name,
			"status": "Delivered",
			"docstatus": doc.docstatus,
			"already_delivered": True,
		}

	if doc.docstatus == 0:
		doc.submit()

	doc.db_set("custom_delivery_status", "Delivered")
	doc.db_set("custom_delivered_on", get_datetime(delivered_on) if delivered_on else now_datetime())

	return {"delivery_note": doc.name, "status": "Delivered", "docstatus": doc.docstatus}
