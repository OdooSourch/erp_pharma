frappe.ui.form.on('Purchase Order', { 
    refresh: function(frm) {
        if (frm.doc.__unsaved) return;

        frappe.call({
            method: "erp_pharma.api.api.get_purchase_value_for_supplier",
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {

                if (!r.message) return;
                let total_value = r.message.total_value || 0;
                let po_list = r.message.purchase_orders || [];

                let allow_management = r.message.allow_management;
                
                frappe.workflow.get_transitions(frm.doc).then((transitions) => {

                    frm.page.clear_actions_menu();

                    transitions.forEach((d) => {

                        if (d.action === "Approve By Management" && !allow_management) {
                            return;
                        }

                        if (d.action === "Approve" && allow_management) {
                            return;
                        }
                        if (frappe.user_roles.includes(d.allowed)) {

                           frm.page.add_action_item(__(d.action), function () {
                                frappe.call({
                                    method: "frappe.model.workflow.apply_workflow",
                                    args: {
                                        doc: frm.doc,
                                        action: d.action
                                    },
                                    callback: function () {
                                        frm.reload_doc();
                                    }
                                });
                           });
                        }

                    });

                });
            }
        });
    }
})