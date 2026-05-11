{
    'name': 'M4FR - Sistem Informasi Keuangan Terintegrasi dan Perpajakan',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Sistem Informasi Keuangan Terintegrasi untuk M4FR by Ataya',
    'author': 'Kelompok 07 - K02',
    'depends': ['sale_management', 'mail'],
    'data': [
        # Security — groups harus paling duluan
        'security/groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence.xml',
        'data/auth_timeout.xml',
        # Reports — D1
        'reports/spk_report.xml',
        # Views — D1
        'views/client_views.xml',
        'views/sale_order_views.xml',
        'views/production_views.xml',
        'views/menu_views.xml',
        # Wizards — D1
        'wizards/update_production_status_wizard_views.xml',
        # Views — D2 (tambahkan saat D2 siap)
        # 'views/invoice_views.xml',
        # 'views/payment_wizard_views.xml',
        # Views — D3 (tambahkan saat D3 siap)
        'views/raw_material_views.xml',
        'views/vendor_bill_views.xml',
        # Views — D4 (tambahkan saat D4 siap)
        # 'views/cash_flow_views.xml',
        # 'views/tax_report_views.xml',
        # Views — D5
        'views/user_management_views.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'm4fr/static/src/js/idle_timeout.js',
            'm4fr/static/src/js/dashboard.js',
            'm4fr/static/src/xml/dashboard.xml',
            'm4fr/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
