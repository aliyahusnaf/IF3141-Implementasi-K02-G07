from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from dateutil.relativedelta import relativedelta
from datetime import date

BULAN = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
         7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

CATEGORY_LABEL = {
    'PENDAPATAN_PESANAN':  'Pendapatan Pesanan',
    'PEMBELIAN_BAHAN_BAKU': 'Pembelian Bahan Baku',
    'BEBAN_OPERASIONAL':   'Beban Operasional',
    'LAINNYA':             'Lainnya',
}


class DashboardController(http.Controller):

    def _check_access(self):
        if not request.env.user.has_group('m4fr.group_m4fr_direktur'):
            raise AccessDenied()

    def _get_period_dates(self, period):
        today = date.today()
        if period == 'last_month':
            end = today.replace(day=1) - relativedelta(days=1)
            start = end.replace(day=1)
        elif period == 'this_quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=quarter_start_month, day=1)
            end = (start + relativedelta(months=3)) - relativedelta(days=1)
        elif period == 'this_year':
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
        else:  # this_month
            start = today.replace(day=1)
            end = (start + relativedelta(months=1)) - relativedelta(days=1)
        return start, end

    def _monthly_breakdown(self, start, end):
        """Bangun list bulan dari start s.d. end, return list of (month_start, month_end, label)."""
        months = []
        cur = start.replace(day=1)
        while cur <= end:
            m_start = cur
            m_end = min((cur + relativedelta(months=1)) - relativedelta(days=1), end)
            months.append((m_start, m_end, BULAN.get(cur.month, str(cur.month))))
            cur = cur + relativedelta(months=1)
        return months

    # ------------------------------------------------------------------
    # KPI
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/kpi', type='json', auth='user')
    def fetch_kpi_data(self, period='this_month'):
        self._check_access()
        start, end = self._get_period_dates(period)
        start_str = start.strftime('%Y-%m-%d')
        end_str   = end.strftime('%Y-%m-%d')

        # Total Pendapatan — sum total_snapshot invoice yang sudah lunas dalam periode
        paid_invoices = request.env['m4fr.invoice'].search([
            ('invoice_status', '=', 'paid'),
            ('issue_date', '>=', start_str),
            ('issue_date', '<=', end_str),
        ])
        total_pendapatan = sum(paid_invoices.mapped('total_snapshot'))

        # Total Pengeluaran — sum cash_flow direction=OUT dalam periode
        outflows = request.env['m4fr.cash.flow'].search([
            ('direction', '=', 'OUT'),
            ('state', '=', 'posted'),
            ('transaction_date', '>=', start_str + ' 00:00:00'),
            ('transaction_date', '<=', end_str + ' 23:59:59'),
        ])
        total_pengeluaran = sum(outflows.mapped('amount'))

        # Pesanan Selesai — sale.order production_status=done dalam periode
        pesanan_selesai = request.env['sale.order'].search_count([
            ('production_status', '=', 'done'),
            ('date_order', '>=', start_str + ' 00:00:00'),
            ('date_order', '<=', end_str + ' 23:59:59'),
        ])

        # Nilai Stok Gudang — stock × standard_unit_price semua bahan baku
        materials = request.env['m4fr.raw.material'].search([])
        nilai_stok = sum(m.stock * m.standard_unit_price for m in materials)

        return {
            'total_pendapatan': total_pendapatan,
            'total_pengeluaran': total_pengeluaran,
            'laba_bersih': total_pendapatan - total_pengeluaran,
            'pesanan_selesai': pesanan_selesai,
            'nilai_stok': nilai_stok,
            'period_start': start_str,
            'period_end': end_str,
        }

    # ------------------------------------------------------------------
    # Chart: Pendapatan vs Pengeluaran per bulan (bar)
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/chart/revenue', type='json', auth='user')
    def chart_revenue(self, period='this_month'):
        self._check_access()
        start, end = self._get_period_dates(period)
        result = []

        for m_start, m_end, label in self._monthly_breakdown(start, end):
            ms = m_start.strftime('%Y-%m-%d')
            me = m_end.strftime('%Y-%m-%d')

            inv = request.env['m4fr.invoice'].search([
                ('invoice_status', '=', 'paid'),
                ('issue_date', '>=', ms),
                ('issue_date', '<=', me),
            ])
            pendapatan = sum(inv.mapped('total_snapshot'))

            out = request.env['m4fr.cash.flow'].search([
                ('direction', '=', 'OUT'),
                ('state', '=', 'posted'),
                ('transaction_date', '>=', ms + ' 00:00:00'),
                ('transaction_date', '<=', me + ' 23:59:59'),
            ])
            pengeluaran = sum(out.mapped('amount'))

            result.append({'bulan': label, 'pendapatan': pendapatan, 'pengeluaran': pengeluaran})

        return result

    # ------------------------------------------------------------------
    # Chart: Tren Laba Bersih per bulan (line)
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/chart/profit', type='json', auth='user')
    def chart_profit(self, period='this_month'):
        self._check_access()
        start, end = self._get_period_dates(period)
        result = []

        for m_start, m_end, label in self._monthly_breakdown(start, end):
            ms = m_start.strftime('%Y-%m-%d')
            me = m_end.strftime('%Y-%m-%d')

            inv = request.env['m4fr.invoice'].search([
                ('invoice_status', '=', 'paid'),
                ('issue_date', '>=', ms),
                ('issue_date', '<=', me),
            ])
            pendapatan = sum(inv.mapped('total_snapshot'))

            out = request.env['m4fr.cash.flow'].search([
                ('direction', '=', 'OUT'),
                ('state', '=', 'posted'),
                ('transaction_date', '>=', ms + ' 00:00:00'),
                ('transaction_date', '<=', me + ' 23:59:59'),
            ])
            pengeluaran = sum(out.mapped('amount'))

            result.append({'bulan': label, 'laba': pendapatan - pengeluaran})

        return result

    # ------------------------------------------------------------------
    # Chart: Komposisi Pengeluaran per kategori (pie)
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/chart/expense-breakdown', type='json', auth='user')
    def chart_expense_breakdown(self, period='this_month'):
        self._check_access()
        start, end = self._get_period_dates(period)
        start_str = start.strftime('%Y-%m-%d')
        end_str   = end.strftime('%Y-%m-%d')

        outflows = request.env['m4fr.cash.flow'].search([
            ('direction', '=', 'OUT'),
            ('state', '=', 'posted'),
            ('transaction_date', '>=', start_str + ' 00:00:00'),
            ('transaction_date', '<=', end_str + ' 23:59:59'),
        ])

        totals = {}
        for flow in outflows:
            totals[flow.category] = totals.get(flow.category, 0.0) + flow.amount

        if not totals:
            return [{'kategori': 'Belum ada data', 'jumlah': 0}]

        return [
            {'kategori': CATEGORY_LABEL.get(cat, cat), 'jumlah': amt}
            for cat, amt in totals.items()
        ]
