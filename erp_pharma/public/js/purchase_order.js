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
                
                if (allow_management && frm.doc.workflow_state !== "Approved") {

                    frm.dashboard.clear_headline();

                    frm.dashboard.set_headline_alert(
                        "PO value exceeds ₹25,00,000. Sent for Management Approval. You will be notified once approved.",
                        "orange"
                    );

                }

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

        if(frm.doc.custom_tat_violation){
            frm.disable_form();
            setTimeout(() => {
                frm.page.clear_actions_menu();
                frm.page.clear_menu();
                frm.clear_custom_buttons();

                if (frm.page.btn_primary) {
                    frm.page.btn_primary.hide();
                }
                $('.workflow-button-group').hide();
                $('.btn-workflow').hide();
            }, 200);
        }
    },
})