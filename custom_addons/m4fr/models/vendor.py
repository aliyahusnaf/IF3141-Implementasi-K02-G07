from odoo import models, fields

class Vendor(models.Model):
    _name = 'm4fr.vendor'
    _description = 'Vendor'

    vendor_id = fields.Char(string='ID Vendor', required=True, copy=False, default='New')
    name = fields.Char(string='Nama Vendor', required=True)
    contact_person = fields.Char(string='Contact Person')
    address = fields.Text(string='Alamat')
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='Nomor Telepon')