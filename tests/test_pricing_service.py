import unittest
from src.pricing import PricingService, PricingError
from src.models import CartItem

class TestPricingService(unittest.TestCase):
    def setUp(self):
        self.service = PricingService()

    def test_subtotal_cents_success(self):
        items = [CartItem("SKU1", 100, 2), CartItem("SKU2", 50, 1)]
        self.assertEqual(self.service.subtotal_cents(items), 250)

    def test_subtotal_cents_invalid_qty(self):
        with self.assertRaises(PricingError):
            self.service.subtotal_cents([CartItem("A", 100, 0)])

    def test_subtotal_cents_negative_price(self):
        with self.assertRaises(PricingError):
            self.service.subtotal_cents([CartItem("A", -10, 1)])

    def test_apply_coupon_variations(self):
        # para ver si es cupon o no vaci
        self.assertEqual(self.service.apply_coupon(1000, None), 1000)
        self.assertEqual(self.service.apply_coupon(1000, "  "), 1000)
        # el save 100
        self.assertEqual(self.service.apply_coupon(1000, "save10"), 900)
        # 2 Lucas
        self.assertEqual(self.service.apply_coupon(5000, "CLP2000"), 3000)
        self.assertEqual(self.service.apply_coupon(1000, "CLP2000"), 0)
        # invalido
        with self.assertRaises(PricingError):
            self.service.apply_coupon(1000, "INVALIDO")

    def test_tax_cents_by_country(self):
        self.assertEqual(self.service.tax_cents(1000, "cl"), 190)
        self.assertEqual(self.service.tax_cents(1000, "EU"), 210)
        self.assertEqual(self.service.tax_cents(1000, "US"), 0)
        with self.assertRaises(PricingError):
            self.service.tax_cents(1000, "JP")

    def test_shipping_cents_thresholds(self):
        # Chile: gratis mayor a 20
        self.assertEqual(self.service.shipping_cents(20000, "CL"), 0)
        self.assertEqual(self.service.shipping_cents(19999, "CL"), 2500)
        # interna
        self.assertEqual(self.service.shipping_cents(100, "US"), 5000)
        self.assertEqual(self.service.shipping_cents(100, "EU"), 5000)
        with self.assertRaises(PricingError):
            self.service.shipping_cents(100, "CN")

    def test_total_cents_integration(self):
        items = [CartItem("A", 10000, 2)] # 20000 total
        # CL: 20000 (neto) + 3800 (tax 19%) + 0 (shipping) = 23800
        self.assertEqual(self.service.total_cents(items, None, "CL"), 23800)