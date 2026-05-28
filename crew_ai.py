"""
crew_ai.py  –  Direct Stripe SDK integration (no MCP/CrewAI agent needed)

We call the Stripe REST API directly using the stripe-python SDK.
This is synchronous, simple, and avoids all async/event-loop issues.
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()


class PaymentProcess:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    async def create_payment_link(
        self,
        amount: float,
        currency: str,
        product_name: str,
        quantity: int,
        customer_email: str,
    ) -> str:
        """
        Create a Stripe payment link directly via the stripe-python SDK.

        Steps:
        1. Create a Product
        2. Create a Price (amount in cents)
        3. Create a Payment Link from that Price
        """
        # 1. Create the product
        product = stripe.Product.create(name=product_name)

        # 2. Create the price  (Stripe needs cents, not dollars)
        amount_cents = int(round(amount * 100))
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount_cents,
            currency=currency.lower(),
        )

        # 3. Create the payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": quantity}],
        )

        return payment_link.url