// Copyright (c) 2026, ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Approval", {
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
