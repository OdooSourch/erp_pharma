# Copyright (c) 2026, ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ERPSetting(Document):
	pass

@frappe.whitelist()
def resume_purchase_order(docname=None):
	reply = {}
	reply['message'] = ""
	try:
		if not docname:
			reply['message'] = "Please save document before resume the purchase order"
			return reply
		
		doc = frappe.get_doc("ERP Setting",docname)
		if doc:
			for purchase in doc.purchase_order:
				frappe.log_error("Purchase Order",purchase.purchase_order)
				if purchase.purchase_order and int(doc.resume_purchase_order): 
					frappe.db.sql("""
						UPDATE `tabPurchase Order`
						SET `custom_tat_violation` = 0
						WHERE `name` = %s 	
					""",(purchase.purchase_order))
			frappe.db.commit()
			reply['message'] = "Purchase Orders Updated Successfully.."
			return reply
	except Exception as e:
		reply['message'] = "Failed to update the purchase orders.."
		frappe.log_error("Error While Updating the purchase order",str(e))
		return reply



	