frappe.ui.form.on('Material Request', {
    custom_purchase_details : function(frm){
        if(!frm.doc.name){
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
                let html = ``;

                html += `
                    <div style="border:2px solid #2c3e50; padding:15px; margin-bottom:20px; border-radius:10px;">
                        <h3 style="color:#2c3e50;">Material Request: ${data.mr_name}</h3>
                `;

                data.items.forEach(mr_item => {

                    let order_color = mr_item.remaining_to_order == 0 ? 'green' : 'red';
                    let receive_color = mr_item.remaining_to_receive == 0 ? 'green' : 'red';

                    html += `
                        <div style="border:1px solid #aaa; padding:10px; margin-top:15px; border-radius:8px;">
                            <h5>Item: ${mr_item.item_code}</h5>

                            <table class="table table-bordered">
                                <tr>
                                    <td><b>MR Qty</b></td>
                                    <td>${mr_item.mr_qty}</td>
                                    <td><b>Ordered Qty</b></td>
                                    <td>${mr_item.ordered_qty}</td>
                                </tr>
                                <tr>
                                    <td><b>Remaining to Order</b></td>
                                    <td colspan="3" style="color:${order_color}; font-weight:bold;">
                                        ${mr_item.remaining_to_order}
                                    </td>
                                </tr>
                            </table>
                    `;

                    mr_item.purchase_orders.forEach(po => {

                        html += `
                            <div style="border:1px solid #3498db; padding:10px; margin-top:10px; border-radius:6px;">
                                <b style="color:#2980b9;">PO:</b> <a style="color:#2980b9;" href="/app/purchase-order/${po.po_name}" target="_blank">
                                    ${po.po_name}
                                </a>

                                <table class="table table-bordered">
                                    <tr>
                                        <td><b>Supplier</b></td>
                                        <td>${po.supplier}</td>
                                        <td><b>Date</b></td>
                                        <td>${formatDate(po.transaction_date)}</td>
                                    </tr>
                                </table>

                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Item Code</th>
                                            <th>PO Qty</th>
                                            <th>Received Qty</th>
                                            <th>Remaining</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;

                        po.items.forEach(po_item => {
                            let po_rem_color = po_item.remaining_to_receive == 0 ? 'green' : 'orange';

                            html += `
                                <tr>
                                    <td>${po_item.item_code}</td>
                                    <td>${po_item.po_qty}</td>
                                    <td>${po_item.received_qty}</td>
                                    <td style="color:${po_rem_color}; font-weight:bold;">
                                        ${po_item.remaining_to_receive}
                                    </td>
                                </tr>
                            `;

                            if (po_item.purchase_receipts.length) {

                                po_item.purchase_receipts.forEach(pr => {

                                    html += `
                                        <tr>
                                            <td colspan="3">
                                                <div style="border:1px dashed #27ae60; padding:8px; margin-top:5px;">
                                                    <b>PR:</b> <a href="/app/purchase-receipt/${pr.pr_name}" target="_blank">${pr.pr_name}</a> | ${formatDate(pr.posting_date)}

                                                    <table class="table table-sm">
                                                        <thead>
                                                            <tr>
                                                                <th>Item</th>
                                                                <th>Qty</th>
                                                                <th>Rate</th>
                                                                <th>Amount</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                    `;

                                    pr.items.forEach(pr_item => {
                                        html += `
                                            <tr>
                                                <td>${pr_item.item_code}</td>
                                                <td>${pr_item.receipt_qty}</td>
                                                <td>${pr_item.rate || 0}</td>
                                                <td>${pr_item.amount || 0}</td>
                                            </tr>
                                        `;
                                    });

                                    html += `
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </td>
                                        </tr>
                                    `;
                                });
                            }

                        });

                        html += `
                                    </tbody>
                                </table>
                            </div>
                        `;
                    });

                    html += `</div>`;
                });

                html += `</div>`;

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