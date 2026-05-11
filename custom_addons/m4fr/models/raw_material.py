from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RawMaterial(models.Model):
    _name = 'm4fr.raw.material'
    _description = 'Master Data Bahan Baku'

    raw_material_id = fields.Char(string='ID Bahan Baku', required=True, copy=False, default='New')
    name = fields.Char(string='Nama Bahan', required=True)
    unit_name = fields.Selection([
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('pcs', 'Pcs')
    ], string='Nama Satuan', required=True)
    standard_unit_price = fields.Float(string='Harga Satuan Standar')
    
    stock = fields.Float(string='Stok', compute='_compute_stock', store=True)
    movement_ids = fields.One2many('m4fr.material.movement', 'raw_material_id')

    @api.depends('movement_ids.quantity', 'movement_ids.type')
    def _compute_stock(self):
        for rec in self:
            total = 0.0
            for move in rec.movement_ids:
                if move.type == 'IN':
                    total += move.quantity
                elif move.type == 'OUT':
                    total -= move.quantity
                elif move.type == 'ADJ':
                    total = move.quantity
            rec.stock = total

    def checkStockAvailability(self, qty):
        if self.stock < qty:
            raise ValidationError(f"Stok {self.name} tidak mencukupi!")
        return True

    def addStock(self, qty):
        self.env['m4fr.material.movement'].recordMovement(self.id, qty, 'IN')

    def reduceStock(self, qty):
        self.checkStockAvailability(qty)
        self.env['m4fr.material.movement'].recordMovement(self.id, qty, 'OUT')

    def updateUnitPrice(self, price):
        self.standard_unit_price = price