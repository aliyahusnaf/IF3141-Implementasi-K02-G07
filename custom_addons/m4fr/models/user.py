import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError

ROLE_GROUP_MAP = {
    'jb01': 'group_m4fr_direktur',
    'jb02': 'group_m4fr_manajer_keuangan',
    'jb03': 'group_m4fr_manajer_produksi',
    'jb04': 'group_m4fr_admin',
    'jb05': 'group_m4fr_kepala_produksi',
}

ROLE_EXTRA_GROUPS = {
    'jb01': 'base.group_erp_manager',
}


class M4FRUser(models.Model):
    _inherit = 'res.users'

    role = fields.Selection([
        ('jb01', 'Direktur (JB-01)'),
        ('jb02', 'Manajer Keuangan (JB-02)'),
        ('jb03', 'Manajer Produksi (JB-03)'),
        ('jb04', 'Admin (JB-04)'),
        ('jb05', 'Kepala Produksi (JB-05)'),
    ], string='Peran Jabatan')

    def _get_all_m4fr_groups(self):
        category = self.env.ref('m4fr.module_category_m4fr', raise_if_not_found=False)
        if not category:
            return self.env['res.groups']
        return self.env['res.groups'].search([('category_id', '=', category.id)])

    def _sync_role_groups(self):
        all_m4fr_groups = self._get_all_m4fr_groups()
        for user in self:
            if not user.role:
                continue
            group_xml = ROLE_GROUP_MAP.get(user.role)
            if not group_xml:
                continue
            new_group = self.env.ref(f'm4fr.{group_xml}')

            cmds = [(3, g.id) for g in (user.groups_id & all_m4fr_groups) if g.id != new_group.id]
            cmds.append((4, new_group.id))
            extra_xml = ROLE_EXTRA_GROUPS.get(user.role)
            if extra_xml:
                extra = self.env.ref(extra_xml, raise_if_not_found=False)
                if extra:
                    cmds.append((4, extra.id))

            user.sudo().write({'groups_id': cmds})

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users.filtered('role')._sync_role_groups()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'role' in vals:
            self._sync_role_groups()
        return res

    def _set_password(self):
        for user in self:
            password = user.password
            if password:
                if len(password) < 8:
                    raise ValidationError("Password harus minimal 8 karakter.")
                if not re.search(r'[a-zA-Z]', password) or not re.search(r'\d', password):
                    raise ValidationError("Password harus mengandung kombinasi huruf dan angka.")
        super()._set_password()

    def check_permission(self, group_xml_id):
        return self.has_group(group_xml_id)

    def assign_role(self, role):
        self.write({'role': role})
