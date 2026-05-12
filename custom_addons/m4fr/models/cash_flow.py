from odoo import models, fields, api

class CashFlow(models.Model):
    _name = 'm4fr.cash.flow'
    _description = 'Buku Besar Arus Kas'
    _order = 'transaction_date desc'

    amount = fields.Float(string='Nominal', required=True)
    category = fields.Selection([
        ('PENDAPATAN_PESANAN', 'Pendapatan Pesanan'),
        ('PEMBELIAN_BAHAN_BAKU', 'Pembelian Bahan Baku'),
        ('BEBAN_OPERASIONAL', 'Beban Operasional'),
        ('LAINNYA', 'Lainnya')
    ], string='Kategori', required=True)
    direction = fields.Selection([
        ('IN', 'Masuk'),
        ('OUT', 'Keluar')
    ], string='Arah (IN/OUT)', required=True)
    transaction_date = fields.Datetime(string='Tanggal Transaksi', default=fields.Datetime.now, required=True)
    note = fields.Text(string='Catatan')
    reference_id = fields.Char(string='ID Referensi')
    reference_model = fields.Char(string='Model Referensi')
    
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('posted', 'Posted')
    ], string='Status', default='posted', readonly=True)

    @api.model
    def createJournalEntry(self, amount, direction, category, reference_id):
        """ Kontrak method yang ditunggu oleh D2 (Invoice) dan D3 (Inventaris) """
        entry = self.create({
            'amount': float(amount),
            'direction': direction,
            'category': category,
            'reference_id': reference_id,
            'state': 'posted'
        })
        return entry

    @api.model
    def getLedgerByPeriod(self, start_date, end_date):
        return self.search([
            ('transaction_date', '>=', start_date),
            ('transaction_date', '<=', end_date),
            ('state', '=', 'posted')
        ])

    @api.model
    def calculateBalance(self):
        entries_in = self.search([('direction', '=', 'IN'), ('state', '=', 'posted')])
        entries_out = self.search([('direction', '=', 'OUT'), ('state', '=', 'posted')])
        return sum(entries_in.mapped('amount')) - sum(entries_out.mapped('amount'))