from odoo import fields, models


class SaleOrderLineM4FR(models.Model):
    _inherit = 'sale.order.line'

    specification = fields.Text(string='Spesifikasi / Desain')
    is_adjustment = fields.Boolean(
        string='Penyesuaian',
        default=False,
        help='Centang jika baris ini adalah biaya/diskon penyesuaian, bukan item pesanan.',
    )
