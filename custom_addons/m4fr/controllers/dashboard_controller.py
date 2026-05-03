from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from dateutil.relativedelta import relativedelta
from datetime import date


class DashboardController(http.Controller):

    def _check_access(self):
        if not request.env.user.has_group('m4fr.group_m4fr_direktur'):
            raise AccessDenied()

    def _get_period_dates(self, period):
        """Return (start_str, end_str) berformat 'YYYY-MM-DD' sesuai period."""
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
        else:  # default: this_month
            start = today.replace(day=1)
            end = (start + relativedelta(months=1)) - relativedelta(days=1)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    # ------------------------------------------------------------------
    # KPI
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/kpi', type='json', auth='user')
    def fetch_kpi_data(self, period='this_month'):
        self._check_access()
        start, end = self._get_period_dates(period)

        # Real query dari D1: pesanan dengan status selesai
        pesanan_selesai = request.env['sale.order'].search_count([
            ('production_status', '=', 'done'),
            ('date_order', '>=', start + ' 00:00:00'),
            ('date_order', '<=', end + ' 23:59:59'),
        ])

        # Dummy data — diganti saat D2 (invoice), D3 (stok), D4 (cashflow) siap
        return {
            'total_pendapatan': 150_000_000,
            'total_pengeluaran': 85_000_000,
            'laba_bersih': 65_000_000,
            'pesanan_selesai': pesanan_selesai,
            'nilai_stok': 45_000_000,
            'period_start': start,
            'period_end': end,
        }

    # ------------------------------------------------------------------
    # Chart data
    # ------------------------------------------------------------------

    @http.route('/m4fr/dashboard/chart/revenue', type='json', auth='user')
    def chart_revenue(self, period='this_month'):
        self._check_access()
        # Dummy data: pendapatan vs pengeluaran per bulan
        # Diganti dengan read_group dari m4fr.cash.flow saat D4 siap
        return [
            {'bulan': 'Jan', 'pendapatan': 12_000_000, 'pengeluaran': 7_500_000},
            {'bulan': 'Feb', 'pendapatan': 15_000_000, 'pengeluaran': 8_200_000},
            {'bulan': 'Mar', 'pendapatan': 18_000_000, 'pengeluaran': 9_100_000},
            {'bulan': 'Apr', 'pendapatan': 14_000_000, 'pengeluaran': 8_800_000},
            {'bulan': 'Mei', 'pendapatan': 20_000_000, 'pengeluaran': 11_000_000},
            {'bulan': 'Jun', 'pendapatan': 22_000_000, 'pengeluaran': 12_500_000},
        ]

    @http.route('/m4fr/dashboard/chart/profit', type='json', auth='user')
    def chart_profit(self, period='this_month'):
        self._check_access()
        # Dummy data: tren laba bersih per bulan
        # Diganti dengan kalkulasi dari m4fr.cash.flow saat D4 siap
        return [
            {'bulan': 'Jan', 'laba': 4_500_000},
            {'bulan': 'Feb', 'laba': 6_800_000},
            {'bulan': 'Mar', 'laba': 8_900_000},
            {'bulan': 'Apr', 'laba': 5_200_000},
            {'bulan': 'Mei', 'laba': 9_000_000},
            {'bulan': 'Jun', 'laba': 9_500_000},
        ]

    @http.route('/m4fr/dashboard/chart/expense-breakdown', type='json', auth='user')
    def chart_expense_breakdown(self, period='this_month'):
        self._check_access()
        # Dummy data: komposisi pengeluaran per kategori
        # Diganti dengan read_group dari m4fr.cash.flow saat D4 siap
        return [
            {'kategori': 'Bahan Baku', 'jumlah': 45_000_000},
            {'kategori': 'Tenaga Kerja', 'jumlah': 25_000_000},
            {'kategori': 'Overhead', 'jumlah': 10_000_000},
            {'kategori': 'Distribusi', 'jumlah': 5_000_000},
        ]
