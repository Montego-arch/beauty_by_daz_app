import frappe
from erpnext.stock.doctype.delivery_note.test_delivery_note import create_delivery_note
from frappe.tests.utils import FrappeTestCase

from beauty_by_daz_app.integrations.shipbubble import update_delivery_status


class TestShipbubble(FrappeTestCase):
	def test_draft_delivery_note_is_submitted_and_flipped_to_delivered(self):
		dn = create_delivery_note(do_not_submit=True)

		result = update_delivery_status(dn.name, "delivered")

		dn.reload()
		self.assertEqual(dn.docstatus, 1)
		self.assertEqual(dn.custom_delivery_status, "Delivered")
		self.assertTrue(dn.custom_delivered_on)
		self.assertEqual(result["status"], "Delivered")

	def test_calling_twice_does_not_error(self):
		dn = create_delivery_note(do_not_submit=True)

		update_delivery_status(dn.name, "delivered")
		result = update_delivery_status(dn.name, "delivered")

		self.assertTrue(result.get("already_delivered"))

	def test_dispatched_status_updates_field_without_submitting(self):
		dn = create_delivery_note(do_not_submit=True)

		result = update_delivery_status(dn.name, "dispatched")

		dn.reload()
		self.assertEqual(dn.docstatus, 0)
		self.assertEqual(dn.custom_delivery_status, "Dispatched")
		self.assertEqual(result["status"], "Dispatched")

	def test_delivery_failed_status_updates_field_without_submitting(self):
		dn = create_delivery_note(do_not_submit=True)

		update_delivery_status(dn.name, "dispatched")
		result = update_delivery_status(dn.name, "delivery failed")

		dn.reload()
		self.assertEqual(dn.docstatus, 0)
		self.assertEqual(dn.custom_delivery_status, "Delivery Failed")
		self.assertEqual(result["status"], "Delivery Failed")

	def test_unrecognised_status_is_ignored(self):
		dn = create_delivery_note(do_not_submit=True)

		result = update_delivery_status(dn.name, "in_transit")

		dn.reload()
		self.assertEqual(dn.docstatus, 0)
		self.assertEqual(dn.custom_delivery_status, "Awaiting Dispatch")
		self.assertTrue(result.get("ignored"))

	def test_cancelled_delivery_note_is_rejected(self):
		dn = create_delivery_note()
		dn.cancel()

		self.assertRaises(frappe.ValidationError, update_delivery_status, dn.name, "delivered")

	def test_unknown_delivery_note_raises_not_found(self):
		self.assertRaises(frappe.DoesNotExistError, update_delivery_status, "DN-DOES-NOT-EXIST", "delivered")

	def test_user_without_write_access_is_rejected(self):
		dn = create_delivery_note(do_not_submit=True)

		user = "test-no-access@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc({"doctype": "User", "email": user, "first_name": "No Access", "roles": []}).insert(
				ignore_permissions=True
			)

		with self.set_user(user):
			self.assertRaises(frappe.PermissionError, update_delivery_status, dn.name, "delivered")
