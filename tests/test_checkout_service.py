import unittest
from unittest.mock import Mock
from src.checkout import CheckoutService, ChargeResult
from src.pricing import PricingError
from src.models import CartItem

class TestCheckoutService(unittest.TestCase):
    def setUp(self):
        self.payments = Mock()
        self.email = Mock()
        self.fraud = Mock()
        self.repo = Mock()
        self.pricing = Mock()
        self.service = CheckoutService(
            self.payments, self.email, self.fraud, self.repo, self.pricing
        )

    def test_checkout_invalid_user(self):
        res = self.service.checkout("  ", [], "tok", "CL")
        self.assertEqual(res, "INVALID_USER")

    def test_checkout_pricing_fails(self):
        self.pricing.total_cents.side_effect = PricingError("pricing_fail")
        res = self.service.checkout("user1", [], "tok", "CL")
        self.assertEqual(res, "INVALID_CART:pricing_fail")

    def test_checkout_rejected_by_fraud(self):
        self.pricing.total_cents.return_value = 1000
        self.fraud.score.return_value = 80
        res = self.service.checkout("user1", [], "tok", "CL")
        self.assertEqual(res, "REJECTED_FRAUD")

    def test_checkout_payment_failed(self):
        self.pricing.total_cents.return_value = 1000
        self.fraud.score.return_value = 10
        self.payments.charge.return_value = ChargeResult(ok=False, reason="Declined")
        res = self.service.checkout("user1", [], "tok", "CL")
        self.assertIn("PAYMENT_FAILED:Declined", res)

    def test_checkout_success_full_flow(self):
        # Configuramos éxito en todas las dependencias
        self.pricing.total_cents.return_value = 5000
        self.fraud.score.return_value = 5
        self.payments.charge.return_value = ChargeResult(ok=True, charge_id="ch_999")
        
        res = self.service.checkout("user1", [], "tok", "CL", "SAVE10")
        
        self.assertTrue(res.startswith("OK:"))
        self.repo.save.assert_called_once()
        self.email.send_receipt.assert_called_once()

    def test_checkout_success_unknown_charge_id(self):
        # Caso para cubrir la rama donde charge_id es None
        self.pricing.total_cents.return_value = 1000
        self.fraud.score.return_value = 0
        self.payments.charge.return_value = ChargeResult(ok=True, charge_id=None)
        
        res = self.service.checkout("user1", [], "tok", "US")
        self.assertTrue(res.startswith("OK:"))