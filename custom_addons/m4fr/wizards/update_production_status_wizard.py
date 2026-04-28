from odoo import api, fields, models
from odoo.exceptions import UserError
from ..models.sale_order import PRODUCTION_STATUS_SEQUENCE, PRODUCTION_STATUS_LABEL


class UpdateProductionStatusWizard(models.TransientModel):
    _name = 'm4fr.update.production.status.wizard'
    _description = 'Wizard Update Status Produksi'

    order_id = fields.Many2one('sale.order', string='Pesanan', required=True, readonly=True)
    current_status = fields.Selection(
        related='order_id.production_status',
        string='Status Saat Ini',
        readonly=True,
    )
    new_status = fields.Selection(
        selection=[
            ('material_received', 'Bahan Diterima'),
            ('cutting', 'Proses Cutting'),
            ('sewing', 'Proses Jahit'),
            ('qc', 'QC'),
            ('done', 'Selesai'),
        ],
        string='Tahap Berikutnya',
        required=True,
        compute='_compute_new_status',
        readonly=False,
        store=True,
    )
    note = fields.Text(string='Catatan (opsional)')

    @api.depends('order_id', 'order_id.production_status')
    def _compute_new_status(self):
        for rec in self:
            if not rec.order_id:
                rec.new_status = False
                continue
            current_idx = PRODUCTION_STATUS_SEQUENCE.index(rec.order_id.production_status)
            if current_idx < len(PRODUCTION_STATUS_SEQUENCE) - 1:
                rec.new_status = PRODUCTION_STATUS_SEQUENCE[current_idx + 1]
            else:
                rec.new_status = rec.order_id.production_status

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        current_idx = PRODUCTION_STATUS_SEQUENCE.index(order.production_status)
        new_idx = PRODUCTION_STATUS_SEQUENCE.index(self.new_status)

        if new_idx != current_idx + 1:
            raise UserError(
                'Status produksi harus diperbarui secara berurutan. '
                f'Tahap berikutnya seharusnya: {PRODUCTION_STATUS_LABEL[PRODUCTION_STATUS_SEQUENCE[current_idx + 1]]}'
            )

        order.production_status = self.new_status
        self.env['m4fr.order.status'].create({
            'order_id': order.id,
            'status': self.new_status,
            'note': self.note or '',
            'changed_by': self.env.user.id,
        })
        return {'type': 'ir.actions.act_window_close'}
