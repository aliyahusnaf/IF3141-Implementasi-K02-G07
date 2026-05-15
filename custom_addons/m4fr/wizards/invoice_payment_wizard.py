from odoo import api, fields, models
from odoo.exceptions import UserError


class M4frInvoicePaymentWizard(models.TransientModel):
    _name = 'm4fr.invoice.payment.wizard'
    _description = 'Wizard Validasi Pembayaran Invoice M4FR'

    invoice_id = fields.Many2one('m4fr.invoice', string='Invoice', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    amount_due = fields.Monetary(
        string='Sisa Tagihan',
        currency_field='currency_id',
        readonly=True,
        compute='_compute_amount_due',
    )
    amount = fields.Monetary(string='Nominal Dibayar', currency_field='currency_id', required=True)
    payment_method = fields.Selection(
        [
            ('transfer', 'Bank Transfer'),
            ('cash', 'Cash'),
        ],
        string='Metode Pembayaran',
        required=True,
        default='transfer',
    )
    payment_date = fields.Date(string='Tanggal Pembayaran', required=True, default=fields.Date.today)
    receipt_url = fields.Char(string='Bukti Pembayaran (URL)')

    @api.depends('invoice_id', 'invoice_id.amount_due')
    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = rec.invoice_id.amount_due

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        invoice_id = self.env.context.get('default_invoice_id') or self.env.context.get('active_id')
        if invoice_id:
            invoice = self.env['m4fr.invoice'].browse(invoice_id)
            res['invoice_id'] = invoice.id
            res['amount'] = invoice.amount_due
        return res

    def action_confirm(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError('Nominal pembayaran harus lebih dari nol.')
        if self.amount > self.amount_due + 0.01:
            raise UserError('Nominal pembayaran tidak boleh melebihi sisa tagihan.')

        payment = self.env['m4fr.order.payment'].create({
            'invoice_id': self.invoice_id.id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date,
            'receipt_url': self.receipt_url,
        })
        payment.validatePayment()
        return {'type': 'ir.actions.act_window_close'}
