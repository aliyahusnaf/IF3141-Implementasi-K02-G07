from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VendorBill(models.Model):
    _name = 'm4fr.vendor.bill'
    _description = 'Tagihan Vendor'

    vendor_bill_id = fields.Char(string='ID Bill', required=True, copy=False, default='New')
    vendor_id = fields.Many2one('m4fr.vendor', string='Vendor', required=True)
    bill_date = fields.Date(string='Tanggal Tagihan', default=fields.Date.today)
    bill_type = fields.Selection([('standard', 'Standar'), ('urgent', 'Urgent')], default='standard')
    payment_status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid')
    ], string='Status Pembayaran', default='draft')

    bill_item_ids = fields.One2many('m4fr.vendor.bill.item', 'vendor_bill_id')
    adjustment_ids = fields.One2many('m4fr.vendor.adjustment', 'vendor_bill_id')
    grand_total = fields.Float(string='Grand Total', compute='_compute_grand_total', store=True)

    @api.model
    def create(self, vals):
        if vals.get('vendor_bill_id', 'New') == 'New':
            vals['vendor_bill_id'] = self.env['ir.sequence'].next_by_code('m4fr.vendor.bill') or 'New'
        return super(VendorBill, self).create(vals)

    @api.depends('bill_item_ids.subtotal', 'adjustment_ids.amount')
    def _compute_grand_total(self):
        for bill in self:
            subtotal_raw = sum(item.subtotal for item in bill.bill_item_ids)
            adjustments = sum(adj.amount for adj in bill.adjustment_ids)
            # Logic: 1.11 * Σ(items) + Σ(adjustments)
            bill.grand_total = (1.11 * subtotal_raw) + adjustments

    def validateBill(self):
        self.payment_status = 'confirmed'

    def processPayment(self):
        for rec in self:
            rec.payment_status = 'paid'
            # UC-09: Trigger D4 Finance automatically after payment
            rec.triggerCashFlowOUT()

    def button_confirm_receipt(self):
        """
        UC-09: Dedicated action for JB-04 or JB-05 to confirm goods arrived.
        This is what actually updates the stock.
        """
        for rec in self:
            if rec.payment_status != 'paid':
                raise ValidationError("Tagihan harus dibayar sebelum konfirmasi penerimaan barang!")
            
            for item in rec.bill_item_ids:
                self.env['m4fr.material.movement'].create({
                    'raw_material_id': item.raw_material_id.id,
                    'vendor_bill_item_id': item.id,
                    'quantity': item.quantity,
                    'type': 'IN',
                    'note': f'Penerimaan Barang: {rec.vendor_bill_id}'
                })

    def triggerCashFlowOUT(self):
        # Wiring to D4
        # self.env['m4fr.cash.flow'].createJournalEntry(self.grand_total, 'OUT', 'PEMBELIAN_BAHAN_BAKU', self.vendor_bill_id)
        pass