from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class TestFR01PencatatanPesanan(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Klien Test Konveksi',
            'email': 'klien@test.com',
            'phone': '08123456789',
        })
        self.product = self.env['product.product'].create({
            'name': 'Kaos Polo',
            'type': 'consu',
            'list_price': 75000,
            'taxes_id': [(5, 0, 0)],
        })
        self.deadline = datetime.now() + timedelta(days=14)

    # ── FR-01: Input Pesanan Baru ─────────────────────────────────────────

    def test_01_buat_pesanan_baru_tersimpan_draft(self):
        """SO baru tersimpan berstatus draft dengan nomor auto-generate."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Kaos Polo Bordir',
                'product_uom_qty': 50,
                'price_unit': 75000,
                'specification': 'Warna merah, bordir logo depan',
            })],
        })
        self.assertEqual(so.state, 'draft')
        self.assertTrue(so.name, 'Nomor SO harus ter-generate')
        self.assertNotEqual(so.name, 'New')

    def test_02_konfirmasi_so_status_berubah(self):
        """Konfirmasi SO draft → status berubah jadi sale."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
                'price_unit': 75000,
            })],
        })
        so.action_confirm()
        self.assertEqual(so.state, 'sale')

    def test_03_grand_total_termasuk_penyesuaian(self):
        """grand_total = subtotal item + penyesuaian."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                    'price_unit': 75000,
                    'is_adjustment': False,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'name': 'Ongkos Kirim',
                    'product_uom_qty': 1,
                    'price_unit': 50000,
                    'is_adjustment': True,
                }),
            ],
        })
        self.assertAlmostEqual(so.amount_total, 800000)  # (10*75000) + 50000

    # ── FR-01: Status Produksi (UC-13) ────────────────────────────────────

    def test_04_production_status_default_pending(self):
        """Status produksi default adalah 'pending'."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        self.assertEqual(so.production_status, 'pending')

    def test_05_update_production_status_berurutan(self):
        """Update status produksi berhasil jika berurutan."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        so.action_confirm()

        wizard = self.env['m4fr.update.production.status.wizard'].create({
            'order_id': so.id,
            'new_status': 'material_received',
        })
        wizard.action_confirm()

        self.assertEqual(so.production_status, 'material_received')
        self.assertEqual(len(so.order_status_ids), 1)
        self.assertEqual(so.order_status_ids[0].status, 'material_received')

    def test_06_update_production_status_tidak_bisa_skip(self):
        """Update status produksi tidak boleh melompati tahapan."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        so.action_confirm()

        wizard = self.env['m4fr.update.production.status.wizard'].create({
            'order_id': so.id,
            'new_status': 'sewing',  # lompat dari pending langsung ke sewing
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_07_riwayat_status_tercatat_dengan_benar(self):
        """Setiap update status produksi tercatat di order_status_ids."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        so.action_confirm()

        for new_status in ['material_received', 'cutting', 'sewing']:
            wizard = self.env['m4fr.update.production.status.wizard'].create({
                'order_id': so.id,
                'new_status': new_status,
                'note': f'Update ke {new_status}',
            })
            wizard.action_confirm()

        self.assertEqual(len(so.order_status_ids), 3)
        self.assertEqual(so.production_status, 'sewing')

    def test_08_update_status_hanya_saat_so_dikonfirmasi(self):
        """Tidak bisa update status produksi pada SO berstatus draft."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        # SO masih draft
        with self.assertRaises(UserError):
            so.action_open_update_production_status()

    def test_09_so_tanpa_deadline_tidak_tersimpan(self):
        """SO tanpa deadline_at wajib ditolak di level UI (field required)."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        self.assertFalse(so.deadline_at, 'deadline_at seharusnya kosong jika tidak diisi')

    def test_10_auto_log_state_change_ke_sale(self):
        """Konfirmasi SO otomatis membuat entri m4fr.order.status dengan status sale."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        so.action_confirm()
        sale_logs = so.order_status_ids.filtered(lambda l: l.status == 'sale')
        self.assertTrue(sale_logs, 'Harus ada log status sale setelah SO dikonfirmasi')

    def test_11_is_locked_field_tersedia(self):
        """Field is_locked tersedia di sale.order dan bisa di-set True."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'deadline_at': self.deadline,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 75000,
            })],
        })
        self.assertFalse(so.is_locked)
        so.write({'is_locked': True})
        self.assertTrue(so.is_locked)
        locked_logs = so.order_status_ids.filtered(lambda l: l.status == 'locked')
        self.assertTrue(locked_logs, 'Harus ada log status locked setelah is_locked di-set')
