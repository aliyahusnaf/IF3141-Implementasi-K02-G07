from odoo import fields, models


class M4FRClient(models.Model):
    _inherit = 'res.partner'

    is_m4fr_client = fields.Boolean(string='Klien M4FR', default=False)

    def action_view_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Riwayat Pesanan',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
        }
