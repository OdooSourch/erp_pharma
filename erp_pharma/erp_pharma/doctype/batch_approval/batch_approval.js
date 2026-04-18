// Copyright (c) 2026, ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Approval", {
    setup : function(frm){
        if (frm.fields_dict.raw_materials) {
            frm.fields_dict.raw_materials.grid.cannot_add_rows = true;
        }
        if (frm.fields_dict.packing_materials) {
            frm.fields_dict.packing_materials.grid.cannot_add_rows = true;
        }
    },
    onload(frm) {
        if (frm.fields_dict.raw_materials) {
            frm.fields_dict.raw_materials.grid.cannot_add_rows = true;
        }
        if (frm.fields_dict.packing_materials) {
            frm.fields_dict.packing_materials.grid.cannot_add_rows = true;
        }
    },
    refresh : function(frm){
        if (frm.fields_dict.raw_materials) {
            frm.fields_dict.raw_materials.grid.cannot_add_rows = true;
        }
        if (frm.fields_dict.packing_materials) {
            frm.fields_dict.packing_materials.grid.cannot_add_rows = true;
        }
    },
	stock_avaiblity : function(frm){
        if(frm.doc.batch_planning && frm.doc.bom && frm.doc.item_code){
            frm.call({
                method : 'check_stock_avaiblity',
                args : {
                    docname : frm.doc.name
                },
                callback : function(r){
                    if(r.message.status_code == 200){
                        frappe.msgprint(r.message)
                        frm.reload_doc()
                    }else{
                        frappe.msgprint(r.message)
                        frm.reload_doc()
                    }
                }
            })
        }
    }
});

frappe.ui.form.on("Extra Items", {
    item_code : function(frm, cdt, cdn){
        let row = locals[cdt][cdn];
        if (row.item_code){
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Item",
                    name: row.item_code
                },
                callback : function(r){
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "item_name", r.message.item_name);
                        frappe.model.set_value(cdt, cdn, "qty", 1);
                    }
                }
            })

            frappe.db.get_single_value("Batch Setting", "rm_source_warehouse")
            .then((warehouse) => {

                if (warehouse) {
                    frappe.call({
                        method: "erpnext.stock.utils.get_stock_balance",
                        args: {
                            item_code: row.item_code,
                            warehouse: warehouse
                        },
                        callback: function(r) {
                            if (r.message !== undefined) {
                                let stock_qty = r.message;

                                frappe.model.set_value(cdt, cdn, "stock_qty", r.message);

                                let qty = row.qty || 0;
                                if (qty <= stock_qty) {
                                    frappe.model.set_value(cdt, cdn, "status", "Present");
                                }else{
                                    frappe.model.set_value(cdt, cdn, "status", "Shortage");
                                }
                            }
                        }
                    });
                }
            });
        }
    },
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.stock_qty !== undefined) {
            if (row.qty <= row.stock_qty) {
                frappe.model.set_value(cdt, cdn, "status", "Present");
            } else {
                frappe.model.set_value(cdt, cdn, "status", "Shortage");
            }
        }
    }
});
