def migrate(cr, version):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    idr = env.ref('base.IDR', raise_if_not_found=False)
    if not idr:
        return
    pricelists = env['product.pricelist'].search([])
    for pl in pricelists:
        vals = {'currency_id': idr.id}
        if 'USD' in pl.name:
            vals['name'] = 'Daftar Harga Publik'
        pl.write(vals)
