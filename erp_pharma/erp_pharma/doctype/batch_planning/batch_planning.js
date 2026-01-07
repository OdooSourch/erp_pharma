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
        console.log("Hello");
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
                    frappe.model.set_value(cdt, cdn, "bom", r.message.default_bom);
                }else{
                    frappe.model.set_value(cdt, cdn, "bom", '');
                }
            }
        })
    }
});