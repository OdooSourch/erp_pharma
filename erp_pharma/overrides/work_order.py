import frappe
from frappe.utils import flt

@frappe.whitelist()
def make_stock_entry(work_order_id, purpose, qty=None, target_warehouse=None):
	work_order = frappe.get_doc("Work Order", work_order_id)
	if not frappe.db.get_value("Warehouse", work_order.wip_warehouse, "is_group"):
		wip_warehouse = work_order.wip_warehouse
	else:
		wip_warehouse = None

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.work_order = work_order_id
	stock_entry.company = work_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = work_order.bom_no
	stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
	# accept 0 qty as well
	stock_entry.fg_completed_qty = (
		qty if qty is not None else (flt(work_order.qty) - flt(work_order.produced_qty))
	)

	if work_order.bom_no:
		stock_entry.inspection_required = frappe.db.get_value("BOM", work_order.bom_no, "inspection_required")

	if purpose == "Material Transfer for Manufacture":
		stock_entry.to_warehouse = wip_warehouse
		stock_entry.project = work_order.project
	else:
		stock_entry.from_warehouse = (
			work_order.source_warehouse
			if work_order.skip_transfer and not work_order.from_wip_warehouse
			else wip_warehouse
		)
		stock_entry.to_warehouse = work_order.fg_warehouse
		stock_entry.project = work_order.project

	if purpose == "Disassemble":
		stock_entry.from_warehouse = work_order.fg_warehouse
		stock_entry.to_warehouse = target_warehouse or work_order.source_warehouse

	stock_entry.set_stock_entry_type()
	stock_entry.get_items()
	for item in stock_entry.items:
		if item.is_finished_item:
			item.use_serial_batch_fields = 1
			query = "SELECT batch FROM `tabBatch Approval` WHERE work_order = '{}'".format(work_order_id)
			results = frappe.db.sql(query,as_dict=True)
			if results:
				item.batch_no = results[0]['batch']
			
	if purpose != "Disassemble":
		stock_entry.set_serial_no_batch_for_finished_good()

	return stock_entry.as_dict()

@frappe.whitelist()
def before_submit(doc,method=None):

	existing_items = [d.item_code for d in doc.required_items]
	
	for row in doc.custom_extra_items:
		if row.item_code not in existing_items:
			doc.append("required_items", {
				"item_code": row.item_code,
				"required_qty": row.required_qty,
				"source_warehouse": row.source_warehouse,
				"stock_uom" : row.stock_uom
			})