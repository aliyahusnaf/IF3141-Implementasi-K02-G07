from odoo import api, fields, models


class M4FROrderStatus(models.Model):
    _name = 'm4fr.order.status'
    _description = 'Riwayat Status Produksi Pesanan'
    _order = 'changed_at desc'

    order_id = fields.Many2one(
        'sale.order',
        string='Pesanan',
        required=True,
        ondelete='cascade',
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('sale', 'Sales Order'),
            ('locked', 'Locked'),
            ('pending', 'Belum Dimulai'),
            ('material_received', 'Bahan Diterima'),
            ('cutting', 'Proses Cutting'),
            ('sewing', 'Proses Jahit'),
            ('qc', 'QC'),
            ('done', 'Selesai'),
        ],
        string='Status',
        required=True,
    )
    changed_at = fields.Datetime(
        string='Waktu Perubahan',
        default=fields.Datetime.now,
        readonly=True,
    )
    note = fields.Text(string='Catatan')
    changed_by = fields.Many2one(
        'res.users',
        string='Diubah Oleh',
        default=lambda self: self.env.user,
        readonly=True,
    )
