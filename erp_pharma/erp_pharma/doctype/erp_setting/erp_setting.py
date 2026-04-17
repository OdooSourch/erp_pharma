# Copyright (c) 2026, ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ERPSetting(Document):
	pass

#Update the visibility of purchase order
@frappe.whitelist()
def resume_purchase_order():
	reply = {}
	reply['message'] = ""
	try:
		# if not docname:
		# 	reply['message'] = "Please save document before resume the purchase order"
		# 	return reply

		purchase_order = frappe.db.get_single_value("ERP Setting","purchase_order")
		if purchase_order:
			frappe.db.sql("""
				UPDATE `tabPurchase Order`
				SET `custom_tat_violation` = 0
				WHERE `name` = %s 	
			""",(purchase_order))

			po_log = frappe.get_doc({
				"doctype": "PO Update Log",
				"reference_doctype":"Purchase Order",
				"reference_name": purchase_order,
				"session_user": frappe.session.user,
				"log_date": frappe.utils.now(),
				"log_type": "TAT PO UPDATE"
			})
			po_log.insert(ignore_permissions=True)
		reply['message'] = "Purchase Orders Updated Successfully.."
		return reply
	except Exception as e:
		reply['message'] = "Failed to update the purchase orders.."
		frappe.log_error("Error While Updating the purchase order",str(e))
		return reply



	