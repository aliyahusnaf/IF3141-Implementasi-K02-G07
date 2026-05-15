from odoo import models, fields, api

class TaxController(models.TransientModel):
    _name = 'm4fr.tax.controller'
    _description = 'Kalkulasi Pajak & Laporan Keuangan'

    period_start = fields.Date(string='Mulai Periode', required=True, default=fields.Date.context_today)
    period_end = fields.Date(string='Akhir Periode', required=True, default=fields.Date.context_today)
    
    gross_omzet = fields.Float(string='Omzet Bruto', compute='_compute_finance_kpi')
    operational_expense = fields.Float(string='Beban Operasional', compute='_compute_finance_kpi')
    net_profit = fields.Float(string='Laba Bersih', compute='_compute_finance_kpi')
    estimated_tax = fields.Float(string='Estimasi Pajak UMKM (0.5%)', compute='_compute_finance_kpi')

    @api.depends('period_start', 'period_end')
    def _compute_finance_kpi(self):
        for record in self:
            domain_in = [('direction', '=', 'IN'), ('state', '=', 'posted')]
            domain_out = [('direction', '=', 'OUT'), ('state', '=', 'posted')]
            
            if record.period_start:
                domain_in.append(('transaction_date', '>=', record.period_start))
                domain_out.append(('transaction_date', '>=', record.period_start))
            if record.period_end:
                domain_in.append(('transaction_date', '<=', record.period_end))
                domain_out.append(('transaction_date', '<=', record.period_end))

            entries_in = self.env['m4fr.cash.flow'].search(domain_in)
            entries_out = self.env['m4fr.cash.flow'].search(domain_out)

            omzet = sum(entries_in.mapped('amount'))
            expense = sum(entries_out.mapped('amount'))

            record.gross_omzet = omzet
            record.operational_expense = expense
            record.net_profit = omzet - expense
            record.estimated_tax = omzet * 0.005  # PP No. 55 Tahun 2022

    def action_print_report(self):
        return self.env.ref('m4fr.action_report_tax_financial').report_action(self)