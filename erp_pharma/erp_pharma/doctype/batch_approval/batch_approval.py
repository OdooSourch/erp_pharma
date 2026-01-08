# Copyright (c) 2026, ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from datetime import datetime
from frappe.model.document import Document


class BatchApproval(Document):
	def on_submit(self):
		self.validate_shortage_qty()
		self.create_stock_entry()
		self.create_batch()
		self.create_work_order()
	
	def validate_shortage_qty(self):
		for row in self.raw_materials:
			if row.status == "Shortage":
				frappe.throw(_("Raw Material {} has a shortage status. Please address the shortage before submitting.".format(row.item_code)))
		
		for row in self.packing_materials:
			if row.status == "Shortage":
				frappe.throw(_("Packing Materials {} has a shortage status. Please address the shortage before submitting.".format(row.item_code)))
		
		if len(self.raw_materials) <= 0 or len(self.packing_materials):
			frappe.throw("Please check the Stock and then proceed further..")

	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.posting_date = getdate()

		for item in self.raw_materials:
			se.append("items",{
				's_warehouse' : frappe.db.get_single_value("Batch Setting",'rm_source_warehouse'),
				't_warehouse' : frappe.db.get_single_value("Batch Setting",'temporary_warehouse'),
				'item_code' : item.item_code,
				'item_name' : item.item_name,
				'qty' : item.qty
			})
		
		for pitem in self.packing_materials:
			se.append("items",{
				's_warehouse' : frappe.db.get_single_value("Batch Setting",'rm_source_warehouse'),
				't_warehouse' : frappe.db.get_single_value("Batch Setting",'temporary_warehouse'),
				'item_code' : pitem.item_code,
				'item_name' : pitem.item_name,
				'qty' : pitem.qty
			})
		
		se.save(ignore_permissions=True)
		se.submit()

		update_query = """UPDATE `tabBatch Approval` SET `stock_entry`=%s WHERE `name`=%s"""
		frappe.db.sql(update_query, (se.name, self.name))
	
	def create_batch(self):

		batch_number = self.generate_batch_number()

		batch = frappe.new_doc("Batch")
		batch.name = batch_number
		batch.item = self.item_code
		batch.use_batchwise_valuation = 1
		batch.save(ignore_permissions=True)

		update_query = """UPDATE `tabBatch Approval` SET `batch`=%s WHERE `name`=%s"""
		frappe.db.sql(update_query, (batch.name,self.name))


	def create_work_order(self):
		wo = frappe.new_doc("Work Order")
		wo.production_item = self.item_code
		wo.bom_no = self.bom
		# wo.custom_stock_entry_type_reference = "Material Transfer"
		wo.qty = self.quantity

		for item in self.raw_materials:
			wo.append("required_items",{
				'item_code' : item.item_code,
				'source_warehouse' : frappe.db.get_single_value("Batch Setting",'temporary_warehouse'),
				'required_qty' : item.qty,
				'include_item_in_manufacturing' : 1
			})
		
		for item in self.packing_materials:
			wo.append("required_items",{
				'item_code' : item.item_code,
				'source_warehouse' : frappe.db.get_single_value("Batch Setting",'temporary_warehouse'),
				'required_qty' : item.qty,
				'include_item_in_manufacturing' : 1
			})
		
		wo.source_warehouse = frappe.db.get_single_value("Batch Setting",'temporary_warehouse')
		wo.fg_warehouse = frappe.db.get_single_value("Batch Setting",'finish_goods_warehouse')
		wo.wip_warehouse = frappe.db.get_single_value("Batch Setting",'wip_warehouse')

		wo.save(ignore_permissions=True)
		wo.submit()

		update_query = """UPDATE `tabBatch Approval` SET `work_order`=%s WHERE `name`=%s"""
		frappe.db.sql(update_query, (wo.name,self.name))

	def generate_batch_number(self):
		today = datetime.now().strftime("%Y-%m-%d")
		
		last_batch_number = frappe.db.sql("""
			SELECT batch FROM `tabBatch Approval`
			WHERE batch LIKE %s 
			ORDER BY batch DESC LIMIT 1				
		""",('BA-' + today + '%',), as_dict=True)

		if last_batch_number:
			last_number = int(last_batch_number[0].batch.split('-')[-1])
			new_number = last_number + 1
		else:
			new_number = 1
		
		batch_numnber = "BA-"+ today + "-" + str(new_number).zfill(8)
		
		return batch_numnber
		# update_query = """UPDATE `tabBatch Approval` SET `batch`=%s WHERE `name`=%s"""
		# frappe.db.sql(update_query, (batch_numnber,self.name))
		

@frappe.whitelist()
def check_stock_avaiblity(docname=None):
	reply = {}
	reply['message'] = ''
	reply['status_code'] = 200

	if not docname:
		reply['message'] = "Please save your document first and click on button"
		reply['status_code'] = 422
		return reply
	
	doc = frappe.get_doc("Batch Approval",docname)
	if not doc:
		reply['message'] = "Document Not Found.."
		reply['status_code'] = 404
		return reply
	
	source_warehouse = frappe.db.get_single_value("Batch Setting",'rm_source_warehouse')
	bom = doc.bom

	if bom:
		bom = frappe.get_doc("BOM",bom)
		for rmpk in bom.items:
			qty = rmpk.qty
			batch_qty = doc.quantity

			total_qty = batch_qty * qty
			frappe.errprint(total_qty)
			stock_qty = frappe.db.get_value("Bin", {'item_code':rmpk.item_code, 'warehouse': source_warehouse},'actual_qty')

			if stock_qty is None:
				stock_qty = 0
			
			item_group = frappe.db.get_value("Item", rmpk.item_code, 'item_group')

			
			if item_group == "Packing Materials":
				item_exists = False
				for item in doc.packing_materials:
					if item.item_code == rmpk.item_code:
						item.qty = total_qty
						item.item_name = rmpk.item_name
						item.stock_qty = stock_qty
						item.status = 'Present' if stock_qty >= qty else 'Shortage'
						item_exists = True
						break
				if not item_exists:
					doc.append('packing_materials',{
						'item_code' : rmpk.item_code,
						'item_name' : rmpk.item_name,
						'stock_qty' : stock_qty,
						'qty' : total_qty,
						'status' : 'Present' if stock_qty >= qty else 'Shortage',
					})
			else:
				item_exists = False
				for item in doc.raw_materials:
					if item.item_code == rmpk.item_code:
						item.qty = total_qty
						item.item_name = rmpk.item_name
						item.stock_qty = stock_qty
						item.status = 'Present' if stock_qty >= qty else 'Shortage'
						item_exists = True
						break
				if not item_exists:
					doc.append('raw_materials',{
						'item_code' : rmpk.item_code,
						'item_name' : rmpk.item_name,
						'stock_qty' : stock_qty,
						'qty' : total_qty,
						'status' : 'Present' if stock_qty >= qty else 'Shortage',
					})
		doc.save()
	reply['message'] = "Data Fetched Successfully!"
	reply['status_code'] = 200
	return reply