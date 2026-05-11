from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError

PRODUCTION_STATUS_SEQUENCE = [
    'pending',
    'material_received',
    'cutting',
    'sewing',
    'qc',
    'done',
]

PRODUCTION_STATUS_LABEL = {
    'pending': 'Belum Dimulai',
    'material_received': 'Bahan Diterima',
    'cutting': 'Proses Cutting',
    'sewing': 'Proses Jahit',
    'qc': 'QC',
    'done': 'Selesai',
}


class SaleOrderM4FR(models.Model):
    _inherit = 'sale.order'

    is_locked = fields.Boolean(
        string='Terkunci',
        default=False,
        tracking=True,
        help='Di-set True oleh D2 setelah pelunasan penuh diterima.',
    )
    deadline_at = fields.Datetime(
        string='Tenggat Waktu',
        tracking=True,
    )
    production_status = fields.Selection(
        selection=[
            ('pending', 'Belum Dimulai'),
            ('material_received', 'Bahan Diterima'),
            ('cutting', 'Proses Cutting'),
            ('sewing', 'Proses Jahit'),
            ('qc', 'QC'),
            ('done', 'Selesai'),
        ],
        string='Status Produksi',
        default='pending',
        tracking=True,
    )
    order_line_items = fields.One2many(
        'sale.order.line', 'order_id',
        domain=[('is_adjustment', '=', False)],
        string='Item Pesanan',
    )
    order_line_adjustments = fields.One2many(
        'sale.order.line', 'order_id',
        domain=[('is_adjustment', '=', True)],
        string='Penyesuaian',
    )
    order_status_ids = fields.One2many(
        'm4fr.order.status', 'order_id',
        string='Riwayat Status Produksi',
    )
    # Computed: tahap produksi berikutnya (untuk ditampilkan di UI)
    next_production_status = fields.Char(
        string='Tahap Berikutnya',
        compute='_compute_next_production_status',
    )
    is_production_done = fields.Boolean(
        compute='_compute_next_production_status',
    )
    status_display = fields.Char(
        string='Status Produksi',
        compute='_compute_status_display',
    )

    @api.depends('state', 'production_status')
    def _compute_status_display(self):
        sale_state_labels = {
            'draft': 'Quotation',
            'sent': 'Quotation Sent',
            'cancel': 'Dibatalkan',
        }
        for rec in self:
            if rec.state in ('sale', 'done'):
                rec.status_display = PRODUCTION_STATUS_LABEL.get(rec.production_status, '')
            else:
                rec.status_display = sale_state_labels.get(rec.state, rec.state)

    @api.depends('production_status')
    def _compute_next_production_status(self):
        for rec in self:
            current_idx = PRODUCTION_STATUS_SEQUENCE.index(rec.production_status)
            if current_idx < len(PRODUCTION_STATUS_SEQUENCE) - 1:
                next_key = PRODUCTION_STATUS_SEQUENCE[current_idx + 1]
                rec.next_production_status = PRODUCTION_STATUS_LABEL[next_key]
                rec.is_production_done = False
            else:
                rec.next_production_status = ''
                rec.is_production_done = True

    def write(self, vals):
        # RBAC Check: Hanya Admin (JB-04) atau Direktur (JB-01) yang boleh mengubah deadline_at
        if 'deadline_at' in vals:
            if not (self.env.user.has_group('m4fr.group_m4fr_admin') or self.env.user.has_group('m4fr.group_m4fr_direktur')):
                raise AccessError("Hanya Admin atau Direktur yang diperbolehkan mengubah Tenggat Waktu.")

        old_states = {rec.id: rec.state for rec in self}
        result = super().write(vals)
        if 'state' in vals or 'is_locked' in vals:
            for rec in self:
                new_state = 'locked' if rec.is_locked else rec.state
                old_state = old_states[get_id] if (get_id := rec.id) in old_states else False
                loggable = {'draft', 'sale', 'locked'}
                if new_state in loggable and old_state != new_state:
                    self.env['m4fr.order.status'].create({
                        'order_id': rec.id,
                        'status': new_state,
                        'changed_by': self.env.user.id,
                    })
        return result

    def action_open_update_production_status(self):
        self.ensure_one()
        # RBAC Check: Hanya Kepala Produksi, Admin, atau Direktur
        if not (self.env.user.has_group('m4fr.group_m4fr_kepala_produksi') or 
                self.env.user.has_group('m4fr.group_m4fr_admin') or 
                self.env.user.has_group('m4fr.group_m4fr_direktur')):
            raise AccessError("Anda tidak memiliki akses untuk memperbarui status produksi.")

        if self.state not in ('sale', 'done'):
            raise UserError('Status produksi hanya bisa diperbarui pada pesanan yang sudah dikonfirmasi.')
        if self.is_production_done:
            raise UserError('Semua tahap produksi sudah selesai.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Status Produksi',
            'res_model': 'm4fr.update.production.status.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def action_create_invoice(self):
        self.ensure_one()
        invoice = self.env['m4fr.invoice'].search([
            ('order_id', '=', self.id),
        ], limit=1)

        if not invoice:
            invoice = self.env['m4fr.invoice'].create({
                'order_id': self.id,
                'total_snapshot': self.amount_total,
                'demand_type': 'percent',
                'demand_value': 50.0,
                'due_date': fields.Date.to_date(self.deadline_at) if self.deadline_at else fields.Date.context_today(self),
            })

        action = self.env.ref('m4fr.action_m4fr_invoice').read()[0]
        action.update({
            'res_id': invoice.id,
            'views': [(self.env.ref('m4fr.view_m4fr_invoice_form').id, 'form')],
            'target': 'current',
        })
        return action
