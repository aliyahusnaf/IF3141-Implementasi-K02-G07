"""
Fields: order_payment_id, invoice_id (M2O), amount, payment_method, payment_date, receipt_url.

Methods: submitPayment(), validatePayment(), and a stub for triggerCashFlowIN() — just add a TODO comment or pass for now.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

class M4frOrderPayment(models.Model):
    _name = 'm4fr.order.payment'
    _description = 'M4FR Order Payment'

    invoice_id = fields.Many2one('m4fr.invoice', string='Invoice', required=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    payment_method = fields.Selection([
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ], string='Payment Method', required=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today)
    receipt_url = fields.Char(string='Receipt URL')

    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError('Payment amount must be greater than zero.')

    def submitPayment(self):
        self.ensure_one()
        # payment record is already saved — nothing extra needed at submit time
        # validation happens in validatePayment()

    def validatePayment(self):
        self.ensure_one()
        invoice = self.invoice_id
        if invoice.invoice_status not in ('posted', 'in_payment'):
            raise UserError('Invoice must be in Posted or In Payment status.')

        other_payments = invoice.payment_ids.filtered(lambda p: p.id != self.id)
        paid_before = sum(other_payments.mapped('amount'))

        if invoice.invoice_status == 'posted':
            if invoice.demand_type == 'percent':
                demand_target = invoice.total_snapshot * (invoice.demand_value / 100)
            else:
                demand_target = invoice.demand_value
            remaining = max(demand_target - paid_before, 0.0)
        else:
            remaining = max(invoice.total_snapshot - paid_before, 0.0)

        if self.amount > remaining + 0.01:  # 1 cent tolerance for float
            raise UserError(
                f'Payment amount ({self.amount}) exceeds remaining balance ({remaining}).'
            )

        if invoice.invoice_status == 'posted':
            invoice.invoice_status = 'in_payment'
        elif invoice.invoice_status == 'in_payment':
            total_paid = paid_before + self.amount
            if total_paid + 0.01 >= invoice.total_snapshot:
                invoice.invoice_status = 'paid'
                # Lock SO saat pelunasan penuh.
                invoice.order_id.is_locked = True
        self.triggerCashFlowIN()

    def triggerCashFlowIN(self):
        self.ensure_one()
        self.env['m4fr.cash.flow'].createJournalEntry(
            amount=self.amount,
            direction='IN',
            category='PENDAPATAN_PESANAN',
            reference_id=self.invoice_id.name,
        )