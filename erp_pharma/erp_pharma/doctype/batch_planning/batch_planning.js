// Copyright (c) 2026, ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Planning", {
	refresh(frm) {
        frm.fields_dict['batch_planning'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
            return {
                filters : {
                    'default_bom': ['!=', '']  
                }
            }
        }
	},
});


frappe.ui.form.on("Batch planning Item", {
	item_code : function(frm, cdt, cdn){
        let row = locals[cdt][cdn];

        frappe.call({
            method: 'frappe.client.get_value',
            args : {
                doctype : 'Item',
                filters : {
                    name : row.item_code
                },
                fieldname : 'default_bom'
            },
            callback : function(r){
                if (r.message && r.message.default_bom){

                    let bom = r.message.default_bom;

                    frappe.model.set_value(cdt, cdn, "bom", r.message.default_bom);
                    frappe.model.set_value(cdt, cdn, "number_of_batch", 1);

                    frappe.call({
                        method: "frappe.client.get_value",
                        args: {
                            doctype: "BOM",
                            filters: {
                                name: bom
                            },
                            fieldname: "custom_quantiity_kg"
                        },
                        callback: function(res) {
                            if (res.message) {
                                console.log(res.message.custom_quantiity_kg)
                                frappe.model.set_value(cdt, cdn, "quantity", res.message.custom_quantiity_kg);
                            }
                        }
                    });
                }else{
                    frappe.model.set_value(cdt, cdn, "bom", '');
                }
            }
        })
    },

    number_of_batch : function(frm,cdt,cdn){
        let row = locals[cdt][cdn];

        if (row.bom) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "BOM",
                    filters: {
                        name: row.bom
                    },
                    fieldname: "custom_quantiity_kg"
                },
                callback: function(r) {

                    if (r.message) {

                        let bom_qty = r.message.custom_quantiity_kg;
                        let total_qty = bom_qty * row.number_of_batch;

                        frappe.model.set_value(cdt, cdn, "quantity", total_qty);
                    }
                }
            });

        }
    }
});