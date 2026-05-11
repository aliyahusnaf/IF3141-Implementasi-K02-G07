from odoo import models, fields, api

class VendorBillItem(models.Model):
    _name = 'm4fr.vendor.bill.item'
    _description = 'Item Tagihan Vendor'

    bill_item_id = fields.Char(string='ID Item', default='New')
    vendor_bill_id = fields.Many2one('m4fr.vendor.bill', ondelete='cascade')
    raw_material_id = fields.Many2one('m4fr.raw.material', string='Bahan Baku')
    quantity = fields.Float(string='Jumlah')
    unit_price = fields.Float(string='Harga Satuan')
    subtotal = fields.Float(string='Subtotal', compute='calculateSubtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def calculateSubtotal(self):
        for item in self:
            item.subtotal = item.quantity * item.unit_price