from django.test import TestCase

from apps.orders.models import Order


class OrderPaymentMethodTests(TestCase):
    def test_payment_method_choices_include_cash_on_delivery(self):
        choices = dict(Order.PAYMENT_METHOD_CHOICES)
        self.assertIn('cod', choices)
        self.assertEqual(choices['cod'], 'Cash on Delivery')
