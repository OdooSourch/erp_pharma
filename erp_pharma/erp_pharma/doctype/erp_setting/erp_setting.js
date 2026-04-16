// Copyright (c) 2026, ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERP Setting", {
	update: function(frm) {
        frappe.call({
            method: 'erp_pharma.erp_pharma.doctype.erp_setting.erp_setting.resume_purchase_order',
            callback: function(r){
                if (r.message){
                    frappe.msgprint(r.message)
                } else {
                    frappe.msgprint("Failed to update purchase order")
                }
            }
        });
	},
});
