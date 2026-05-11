from odoo import models, fields, api

class Vendor(models.Model):
    _name = 'm4fr.vendor'
    _description = 'Master Data Vendor'

    name = fields.Char(string='Nama Vendor', required=True)
    contact_name = fields.Char(string='Contact Person')
    phone = fields.Char(string='Nomor Telepon')
    email = fields.Char(string='Email')
    address = fields.Text(string='Alamat')

class VendorBill(models.Model):
    _name = 'm4fr.vendor.bill'
    _description = 'Tagihan Vendor'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Optional: for chatter

    name = fields.Char(string='Nomor Tagihan', required=True, copy=False, readonly=True, default='New')
    vendor_id = fields.Many2one('m4fr.vendor', string='Vendor', required=True)
    date_bill = fields.Date(string='Tanggal Tagihan', default=fields.Date.context_today)
    
    bill_item_ids = fields.One2many('m4fr.vendor.bill.item', 'bill_id', string='Item Pembelian')
    
    grand_total = fields.Float(string='Grand Total', compute='_compute_grand_total', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid')
    ], string='Status', default='draft', tracking=True)

    @api.depends('bill_item_ids.subtotal')
    def _compute_grand_total(self):
        for bill in self:
            bill.grand_total = sum(item.subtotal for item in bill.bill_item_ids)

    def action_confirm(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('m4fr.vendor.bill') or 'BILL/' + str(fields.Date.today())
            rec.state = 'confirmed'

    def action_pay(self):
        for rec in self:
            # Logic for FR-04: Increase stock when paid
            for item in rec.bill_item_ids:
                item.material_id.stock += item.quantity
            
            # TODO: Call D4.createJournalEntry here in the next step
            rec.state = 'paid'

class VendorBillItem(models.Model):
    _name = 'm4fr.vendor.bill.item'
    _description = 'Item Tagihan Vendor'

    bill_id = fields.Many2one('m4fr.vendor.bill', string='Bill Reference', ondelete='cascade')
    material_id = fields.Many2one('m4fr.raw.material', string='Bahan Baku', required=True)
    quantity = fields.Float(string='Jumlah', default=1.0)
    unit_price = fields.Float(string='Harga Satuan')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for item in self:
            item.subtotal = item.quantity * item.unit_price