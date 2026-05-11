{
    'name': 'M4FR - Sistem Informasi Keuangan Terintegrasi dan Perpajakan',
    'version': '17.0.1.0.1',
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
        'data/company_currency.xml',
        # Reports — D1
        'reports/spk_report.xml',
        # Reports — D4
        'reports/tax_report_template.xml',
        'reports/invoice_reports.xml',
        # Views — D1
        'views/client_views.xml',
        'views/sale_order_views.xml',
        'views/production_views.xml',
        'views/menu_views.xml',
        # Wizards — D1
        'wizards/update_production_status_wizard_views.xml',
        # Views — D2 (tambahkan saat D2 siap)
        'views/invoice_views.xml',
        'views/payment_wizard_views.xml',
        # Views — D3 (tambahkan saat D3 siap)
        # 'views/raw_material_views.xml',
        # 'views/vendor_bill_views.xml',
        # Views — D4 (tambahkan saat D4 siap)
        'views/cash_flow_views.xml',
        'views/tax_report_views.xml',
        # Views — D5 (tambahkan saat D5 siap)
        # 'views/dashboard_views.xml',
        # 'views/user_management_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
