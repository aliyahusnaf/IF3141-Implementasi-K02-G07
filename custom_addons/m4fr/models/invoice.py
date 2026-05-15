"""Fields: invoice_id, order_id (M2O), total_snapshot, amount_due (computed), invoice_status enum (draft/posted/in_payment/paid), demand_type enum (percent/flat), demand_value, issue_date, due_date.

Methods: generateFromOrder(), postInvoice(), registerPayment(), calculateAmountDue()"""

from odoo import models, fields, api
from odoo.exceptions import UserError

class M4frInvoice(models.Model):
    _name = 'm4fr.invoice'
    _description = 'M4FR Invoice'

    name = fields.Char(string='Invoice Number', readonly=True, copy=False, default='New')
    order_id = fields.Many2one('sale.order', string='Sales Order', required=True)
    total_snapshot = fields.Monetary(string='Order Total (Snapshot)', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    demand_type = fields.Selection([('percent', 'Percentage'), ('flat', 'Flat')], default='percent')
    demand_value = fields.Float(string='DP Value', default=50.0)
    amount_due = fields.Monetary(string='Amount Due', compute='_compute_amount_due', store=True)
    invoice_status = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
    ], default='draft', string='Status')
    state = fields.Selection(
        related='invoice_status',
        store=True,
        readonly=True,
    )
    issue_date = fields.Date(string='Issue Date', default=fields.Date.today)
    due_date = fields.Date(string='Due Date')
    payment_ids = fields.One2many('m4fr.order.payment', 'invoice_id', string='Payments')
    sent_at = fields.Datetime(string='Sent At', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('m4fr.invoice') or 'New'
        return super().create(vals_list)

    @api.depends('total_snapshot', 'demand_type', 'demand_value', 'payment_ids.amount', 'invoice_status')
    def _compute_amount_due(self):
        for rec in self:
            paid = sum(rec.payment_ids.mapped('amount'))
            if rec.invoice_status in ('draft', 'posted'):
                # Tahap awal invoice: amount_due merepresentasikan sisa DP/termin awal.
                if rec.demand_type == 'percent':
                    demand_target = rec.total_snapshot * (rec.demand_value / 100)
                else:
                    demand_target = rec.demand_value
                rec.amount_due = max(demand_target - paid, 0.0)
            else:
                # Tahap pelunasan: amount_due merepresentasikan sisa total invoice.
                rec.amount_due = max(rec.total_snapshot - paid, 0.0)

    @api.model
    def generateFromOrder(self, order_id):
        order = self.env['sale.order'].browse(order_id)
        if order.state != 'sale':
            raise UserError('Invoice can only be created from a confirmed Sales Order.')
        invoice = self.create({
            'order_id': order.id,
            'total_snapshot': order.amount_total,
            'demand_type': 'percent',
            'demand_value': 50.0,
        })
        # auto-generate sequence number
        invoice.name = self.env['ir.sequence'].next_by_code('m4fr.invoice') or 'New'
        return invoice

    def postInvoice(self):
        self.ensure_one()
        if self.invoice_status != 'draft':
            raise UserError('Only draft invoices can be confirmed.')
        self.invoice_status = 'posted'

    def registerPayment(self, payment):
        self.ensure_one()
        payment.invoice_id = self.id

    def action_open_payment_wizard(self):
        self.ensure_one()
        if self.invoice_status not in ('posted', 'in_payment'):
            raise UserError('Payment can only be registered for posted or in-payment invoices.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Validasi Pembayaran',
            'res_model': 'm4fr.invoice.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_invoice_id': self.id},
        }

    def action_send_invoice(self):
        """UC-04: generate PDF and log send timestamp."""
        self.ensure_one()
        if self.invoice_status != 'posted':
            raise UserError('Only posted invoices can be sent.')
        report = self.env.ref('m4fr.action_report_invoice')
        # log timestamp
        self.sent_at = fields.Datetime.now()
        # return report action so Odoo downloads/opens the PDF
        return report.report_action(self)