from odoo import models, fields

class RawMaterial(models.Model):
    _name = 'm4fr.raw.material' # This becomes the DB table name
    _description = 'Master Data Bahan Baku'

    name = fields.Char(string='Nama Bahan', required=True)
    stock = fields.Float(string='Stok Saat Ini', default=0.0)
    unit = fields.Selection([
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('pcs', 'Pcs')
    ], string='Satuan')