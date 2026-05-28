import os
import httpx
from uagents import Agent, Context, Field, Model
from payment_model import PaymentRequest, PaymentResponse
from nl_parser import extract_payment_details

USER_AGENT_SEED_PHRASE = "USER_AGENT_SEED_PHRASE"
GENERATE_PAYMENT_LINK_URL = "http://localhost:8000/generate_payment_link"

user_agent = Agent(
    name="User Agent",
    seed=USER_AGENT_SEED_PHRASE,
)

class UserRequest(Model):
    amount: float
    product_name: str
    quantity: int
    email: str

class UserResponse(Model):
    status: str = Field(
        description="Status of the user request.",
        choices=["success", "pending", "error"]
    )
    details: str = Field(description="Additional details about the request status.")
    payment_link: str = Field(description="URL of the payment link.")

@user_agent.on_rest_post("/create_payment", UserRequest, UserResponse)
async def handle_user_request(ctx: Context, req: UserRequest) -> UserResponse:
    ctx.logger.info(f"Received user request. Details: {req}")

    payment_request = PaymentRequest(
        amount=req.amount,
        currency="USD",
        product_name=req.product_name,
        quantity=req.quantity,
        customer_email=req.email
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GENERATE_PAYMENT_LINK_URL,
                json=payment_request.dict()
            )
            response_data = response.json()

            return UserResponse(status=response_data["status"], details=response_data["details"], payment_link=response_data["payment_link"])
    except Exception as e:
     return UserResponse(
        status="error",
        details=str(e),
        payment_link=""
     )

@user_agent.on_rest_post("/payment_confirmation", PaymentResponse, UserResponse)
async def handle_payment_confirmation(ctx: Context, resp: PaymentResponse) -> UserResponse:
    ctx.logger.info(f"Received payment confirmation. Details: {resp}")
    return UserResponse(status=resp.status, details=resp.details, payment_link=resp.payment_link)


# ── Natural-language payment endpoint ────────────────────────────────────────

class NLPaymentRequest(Model):
    """Accepts a free-text payment prompt."""
    prompt: str


@user_agent.on_rest_post("/create_payment_nl", NLPaymentRequest, UserResponse)
async def handle_nl_payment(ctx: Context, req: NLPaymentRequest) -> UserResponse:
    """
    Natural-language payment endpoint.

    1. Use Groq LLM to extract structured fields from the prompt.
    2. Pass them into the existing /generate_payment_link flow unchanged.
    """
    ctx.logger.info(f"Received NL payment request: {req.prompt!r}")

    # Step 1 – AI extraction
    try:
        parsed = extract_payment_details(req.prompt)
    except ValueError as exc:
        return UserResponse(status="error", details=str(exc), payment_link="")

    ctx.logger.info(
        f"NL extracted: amount={parsed['amount']}, "
        f"product={parsed['product_name']!r}, email={parsed['email']!r}, "
        f"quantity={parsed['quantity']}"
    )

    # Step 2 – Feed into the existing Stripe payment flow (unchanged)
    payment_request = PaymentRequest(
        amount=parsed["amount"],
        currency="USD",
        product_name=parsed["product_name"],
        quantity=parsed["quantity"],
        customer_email=parsed["email"],
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GENERATE_PAYMENT_LINK_URL,
                json=payment_request.dict(),
            )
            response_data = response.json()

        return UserResponse(
            status=response_data["status"],
            details=response_data["details"],
            payment_link=response_data.get("payment_link", ""),
        )
    except Exception as exc:
        return UserResponse(status="error", details=str(exc), payment_link="")

if __name__ == "__main__":
    user_agent.run()