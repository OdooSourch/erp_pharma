# Copyright (c) 2026, ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BatchPlanning(Document):
	def before_submit(self):
		for item in self.batch_planning:
			number_of_batch = int(item.number_of_batch)
			
			if number_of_batch <= 0:
				frappe.throw(_("Please Enter a Valid Batch Pack"))
			
			existing_batch_approvals = frappe.get_all("Batch Approval", filters={'batch_planning' : self.name, 'item_code':item.item_code},)
			existing_count = len(existing_batch_approvals)

			remaining_batches_to_create = number_of_batch - existing_count

			if remaining_batches_to_create > 0:
				for i in range(number_of_batch):
					qty = item.quantity / number_of_batch
					batch_approval = frappe.new_doc("Batch Approval")
					batch_approval.batch_planning = self.name
					batch_approval.number_of_batch = int(1)
					batch_approval.item_code = item.item_code
					batch_approval.bom = item.bom	
					batch_approval.quantity = qty #item.quantity
					batch_approval.save(ignore_permissions=True)
			else:
				frappe.msgprint("All required Batch Approvals are already created")

		frappe.msgprint(f"Batch Approval documents created for {len(self.batch_planning)} items.")
