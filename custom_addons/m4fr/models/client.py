from odoo import api, fields, models

class M4FRClient(models.Model):
    _name = 'm4fr.client'
    _description = 'M4FR Pelanggan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nama Pelanggan', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='No. Kontak', tracking=True)
    address = fields.Text(string='Alamat', tracking=True)
    city = fields.Char(string='Kota', tracking=True)
    
