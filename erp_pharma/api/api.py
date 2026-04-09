import frappe
from datetime import datetime,timedelta

#Material Request Purchase Order Details
@frappe.whitelist()
def get_purchase_data(docname=None, supplier=None):

    reply = {}
    reply['message'] = ''
    reply['data'] = []

    if not docname:
        reply['message'] = "Please save the document before showing the purchase data..!"
        return reply

    doc = frappe.get_doc("Material Request", docname)

    mr_items = frappe.db.sql("""
        SELECT 
            name,
            item_code,
            qty,
            ordered_qty
        FROM `tabMaterial Request Item`
        WHERE parent = %s
    """, doc.name, as_dict=True)

    if not mr_items:
        reply['message'] = "No Material Request Items found"
        return reply

    purchase_data = frappe.db.sql("""
        SELECT 
            poi.material_request_item,
            po.name AS po_name,
            po.transaction_date,
            po.supplier,

            poi.name AS po_item,
            poi.item_code,
            poi.item_name,
            poi.qty AS po_qty,
            poi.received_qty,

            pr.name AS pr_name,
            pr.posting_date,

            pri.name AS pr_item,
            pri.item_code AS pr_item_code,
            pri.qty AS receipt_qty,
            pri.rate,
            pri.amount

        FROM `tabPurchase Order Item` poi

        INNER JOIN `tabPurchase Order` po 
            ON po.name = poi.parent

        LEFT JOIN `tabPurchase Receipt Item` pri 
            ON pri.purchase_order = po.name 
            AND pri.purchase_order_item = poi.name

        LEFT JOIN `tabPurchase Receipt` pr 
            ON pr.name = pri.parent

        WHERE poi.material_request = %s
    """, doc.name, as_dict=True)

    mr_structure = {
        "mr_name": doc.name,
        "items": []
    }

    mr_item_map = {}
    mr_received_map = {}

    for mr in mr_items:
        mr_item_map[mr["name"]] = {
            "mr_item_name": mr["name"],
            "item_code": mr["item_code"],
            "mr_qty": mr["qty"],
            "ordered_qty": mr["ordered_qty"],
            "remaining_to_order": (mr["qty"] or 0) - (mr["ordered_qty"] or 0),
            "purchase_orders": []
        }


    for row in purchase_data:
        mr_key = row["material_request_item"]
        mr_item = mr_item_map.get(mr_key)

        mr_item = mr_item_map.get(row["material_request_item"])
        if not mr_item:
            continue
        
        if row["pr_item"]:
            mr_received_map[mr_key] = mr_received_map.get(mr_key, 0) + (row["receipt_qty"] or 0)

        po_list = mr_item["purchase_orders"]
        po = next((p for p in po_list if p["po_name"] == row["po_name"]), None)

        if not po:
            po = {
                "po_name": row["po_name"],
                "transaction_date": row["transaction_date"],
                "supplier": row["supplier"],
                "items": []
            }
            po_list.append(po)

        po_item_list = po["items"]
        po_item = next((i for i in po_item_list if i["item_code"] == row["item_code"]), None)

        if not po_item:
            po_item = {
                "item_code": row["item_code"],
                "item_name" : row['item_name'],
                "po_qty": row["po_qty"],
                "received_qty": row["received_qty"],
                "remaining_to_receive": (row["po_qty"] or 0) - (row["received_qty"] or 0),
                "purchase_receipts": []
            }
            po_item_list.append(po_item)

        if row["pr_name"]:
            pr_list = po_item["purchase_receipts"]

            pr = next((p for p in pr_list if p["pr_name"] == row["pr_name"]), None)

            if not pr:
                pr = {
                    "pr_name": row["pr_name"],
                    "posting_date": row["posting_date"],
                    "items": []
                }
                pr_list.append(pr)

            if row["pr_item"]:
                pr_item_list = pr["items"]

                pr_item = next(
                    (i for i in pr_item_list if i["pr_item"] == row["pr_item"]),
                    None
                )

                if not pr_item:
                    pr_item = {
                        "pr_item": row["pr_item"],
                        "item_code": row["pr_item_code"],
                        "receipt_qty": row["receipt_qty"],
                        "rate": row["rate"],
                        "amount": row["amount"]
                    }
                    pr_item_list.append(pr_item)
    for mr_name, mr_item in mr_item_map.items():
        total_received = mr_received_map.get(mr_name, 0)
        
        mr_item["received_qty"] = total_received
        mr_item["remaining_to_receive"] = (mr_item["mr_qty"] or 0) - total_received

    mr_structure["items"] = list(mr_item_map.values())
    reply["data"] = mr_structure

    return reply


#Workflow Approval Conditions
@frappe.whitelist()
def get_purchase_value_for_supplier(docname=None):

    reply = {}
    reply['message'] = ''

    if not docname:
        reply['message'] = "Please save the document first and then further process.."
        return reply

    doc = frappe.get_doc("Purchase Order", docname)

    if not doc.supplier:
        reply['message'] = "Supplier Not found.."
        return reply

    query = """
        SELECT name, grand_total
        FROM `tabPurchase Order`
        WHERE supplier = %s
          AND name != %s
          AND docstatus = 0
        ORDER BY transaction_date DESC
        LIMIT 2
    """

    results = frappe.db.sql(query, (doc.supplier, doc.name), as_dict=True)
    current_value = doc.grand_total or 0
    
    total_value = current_value + sum(row.grand_total for row in results)

    allow_management = total_value >= 2500000

    return {
        "message": "Success",
        "purchase_orders": results,
        "total_value": total_value,
        "allow_management" : allow_management
    }


#Cron to check the purchase order time and hold on it.
@frappe.whitelist()
def cron_purchase_order():
    reply = {}
    reply['message'] = ""

    try:
        query = "SELECT name, creation FROM `tabPurchase Order` WHERE docstatus = 0 "
        results = frappe.db.sql(query,as_dict=True)
        if results:
            for po in results:
                creation_time = po['creation']
                if creation_time:
                    creation_time_obj = datetime.strptime(str(creation_time), "%Y-%m-%d %H:%M:%S.%f")
                    current_time_obj = datetime.now()
                    time_difference = current_time_obj - creation_time_obj
                    if time_difference > timedelta(hours=24):
                        frappe.log_error("Purchase Order",po['name'])
                        frappe.db.sql("""
                            UPDATE `tabPurchase Order`
                            SET `custom_tat_violation` = 1
                            WHERE `name` = %s 
                        """, (po['name']))
                        frappe.db.commit()
    except Exception as e:
        frappe.log_error(str(e), "Cron Purchase Order Error")
