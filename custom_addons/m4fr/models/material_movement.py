from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MaterialMovement(models.Model):
    _name = 'm4fr.material.movement'
    _description = 'Pergerakan Bahan Baku'

    movement_id = fields.Char(string='ID Movement', required=True, copy=False, default='New')
    raw_material_id = fields.Many2one('m4fr.raw.material', string='Bahan Baku', required=True)
    vendor_bill_item_id = fields.Many2one('m4fr.vendor.bill.item', string='Item Bill', ondelete='set null')
    order_id = fields.Many2one('sale.order', string='Pesanan', ondelete='set null')
    
    quantity = fields.Float(string='Jumlah', required=True)
    type = fields.Selection([('IN', 'IN'), ('OUT', 'OUT'), ('ADJUSTMENT', 'ADJUSTMENT')], string='Tipe', required=True)
    movement_date = fields.Datetime(string='Tanggal Mutasi', default=fields.Datetime.now)
    note = fields.Char(string='Catatan')

    @api.model
    def create(self, vals):
        if vals.get('movement_id', 'New') == 'New':
            vals['movement_id'] = self.env['ir.sequence'].next_by_code('m4fr.material.movement') or 'New'
        return super(MaterialMovement, self).create(vals)
    
    @api.model
    def recordMovement(self, mat_id, qty, m_type):
        return self.create({
            'raw_material_id': mat_id,
            'quantity': qty,
            'type': m_type,
        })

    def processStockUpdate(self):
        # In Odoo, since stock is 'store=True' and depends on movement_ids,
        # it updates automatically on creation/edit.
        pass

    @api.constrains('quantity', 'type', 'raw_material_id')
    def _check_qty_out(self):
        for rec in self:
            if rec.type == 'OUT':
                available = rec.raw_material_id.stock + (rec._origin.quantity if rec.id else 0)
                if rec.quantity > available:
                    raise ValidationError(f"Jumlah keluar ({rec.quantity}) melebihi stok tersedia ({available})!")