frappe.ui.form.on('Material Request', {
    custom_purchase_details : function(frm){
        if(frm.is_new()){
            frappe.msgprint("Please save the document before showing the purchase details")
            return
        }

        let d = new frappe.ui.Dialog({
            title: __("Purchase Order Details"),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "po_details",
                }
            ],
            size: 'extra-large',
            primary_action_label: __("Close"),
            primary_action: () => d.hide()
        });

        d.show();

        frappe.call({
            method: 'erp_pharma.api.api.get_purchase_data',
            args: {
                docname: frm.doc.name
            },
            callback: function (r) {
                if (!r.message || !r.message.data || !r.message.data.items.length) {
                    frappe.msgprint("No purchase data found against this Material Request");
                    return;
                }

                let data = r.message.data;
                let html = `
                    <div class="alert alert-info" style="font-size:14px;">
                        <b>Purchase Orders created against this Material Request</b>
                    </div>

                    <table class="table table-bordered">
                        <thead>
                            <tr style="background:#f5f5f5;">
                                <th>Purchase Order</th>
                                <th>Item Code</th>
                                <th>Item Name</th>
                                <th>Ordered Qty</th>
                                <th>Received Qty</th>
                                <th>Pending Qty</th>
                                <th>Schedule Date</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                let total_ordered = 0;
                let total_received = 0;
                let total_pending = 0;

                data.items.forEach(mr_item => {
                    mr_item.purchase_orders.forEach(po => {
                        po.items.forEach(po_item => {

                            let pending = po_item.po_qty - po_item.received_qty;
                            let link = `<a href="/app/purchase-order/${po.po_name}" target="_blank" style="color:#2980b9;">${po.po_name}</a>`;

                            html += `
                                <tr>
                                    <td>${link}</td>
                                    <td>${po_item.item_code}</td>
                                    <td>${po_item.item_name || ""}</td>
                                    <td>${po_item.po_qty}</td>
                                    <td>${po_item.received_qty}</td>
                                    <td>${pending}</td>
                                    <td>${formatDate(po.transaction_date)}</td>
                                </tr>
                            `;

                            total_ordered += po_item.po_qty;
                            total_received += po_item.received_qty;
                            total_pending += pending;
                        });
                    });
                });

                html += `
                        </tbody>
                        <tfoot>
                            <tr style="background:#f5f5f5; font-weight:bold;">
                                <td colspan="3" style="text-align:right;">Total</td>
                                <td>${total_ordered}</td>
                                <td>${total_received}</td>
                                <td>${total_pending}</td>
                                <td></td>
                            </tr>
                        </tfoot>
                    </table>
                `;

                d.fields_dict.po_details.$wrapper.html(html);
            }
        });

    }
})

function formatDate(dateStr) {
    if (!dateStr) return '';
    let d = new Date(dateStr);
    let day = String(d.getDate()).padStart(2, '0');
    let month = String(d.getMonth() + 1).padStart(2, '0');
    let year = d.getFullYear();
    return `${day}-${month}-${year}`;
}