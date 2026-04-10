// Copyright (c) 2026, ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERP Setting", {
	update: function(frm) {
        if(frm.doc.__unsaved){
            frappe.throw("Please save document first")
        }else{
            frappe.call({
                method : 'erp_pharma.erp_pharma.doctype.erp_setting.erp_setting.resume_purchase_order',
                args : {
                    docname : frm.doc.name
                },
                callback : function(r){
                    if(r.message){
                        frappe.msgprint(r.message)
                    }else{
                        frappe.msgprint("failed to updating purchase order")
                    }
                }
            })
        }
	},
});
