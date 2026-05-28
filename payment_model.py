from uagents import Field, Model

from typing import Optional

class PaymentRequest(Model):
    amount: float = Field(description="Amount to be charged.")
    currency: str = Field(description="Currency (e.g., USD, EUR).")
    product_name: str = Field(description="Name of the product.")
    quantity: int = Field(description="Quantity of the product.")
    customer_email: str = Field(description="Email of the customer.")

class PaymentResponse(Model):
    status: str = Field(
        description="Status of the payment.",
        choices=["success", "pending", "error"]
    )
    details: str = Field(description="Details of the payment (e.g., confirmation or processing details).")
    payment_link: Optional[str] = Field(default="", description="URL of the payment link.")
    generate_time: Optional[int] = Field(default=0, description="Timestamp when the payment link was generated.")
    payment_status: Optional[str] = Field(default="", description="Current status of the payment.")
    confirmation_time: Optional[int] = Field(default=0, description="Timestamp when the payment was confirmed.")
    amount: Optional[float] = Field(default=0.0, description="Amount charged.")