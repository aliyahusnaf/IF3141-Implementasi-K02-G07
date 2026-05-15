from odoo import models, fields, api

class VendorAdjustment(models.Model):
    _name = 'm4fr.vendor.adjustment'
    _description = 'Adjustment Vendor'

    vendor_adjustment_id = fields.Char(string='ID Adjustment', default='New')
    vendor_bill_id = fields.Many2one('m4fr.vendor.bill', ondelete='cascade')
    adjustment_name = fields.Char(string='Nama Penyesuaian')
    amount = fields.Float(string='Nominal')