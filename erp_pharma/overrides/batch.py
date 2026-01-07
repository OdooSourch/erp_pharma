from erpnext.stock.doctype.batch.batch import Batch # type: ignore
from datetime import datetime
import frappe

class CustomBatch(Batch):
    def autoname(self):
        """Override the autoname method for Batch to generate custom batch ID"""

        if self.batch_id:
            self.name = self.batch_id
            return

        self.batch_id = self.generate_batch_number()

        if frappe.db.exists("Batch", self.batch_id):
            self.batch_id = None 

        self.name = self.batch_id


    def generate_batch_number(self):
        today = datetime.now().strftime("%Y-%m-%d")

        last_batch_number = frappe.db.sql("""
            SELECT name FROM `tabBatch`
            WHERE name LIKE %s
            ORDER BY name DESC LIMIT 1
        """, ('BA-' + today + '%',), as_dict=True)

        if last_batch_number:
            last_number = int(last_batch_number[0].name.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        batch_number = f"BA-{today}-{str(new_number).zfill(8)}"
        return batch_number
    