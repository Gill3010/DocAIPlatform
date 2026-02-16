

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest, OrdersGetRequest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from datetime import datetime, timedelta

# Initialize PayPal
client_id = settings.PAYPAL_CLIENT_ID
client_secret = settings.PAYPAL_CLIENT_SECRET
if settings.PAYPAL_MODE == "live":
    environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
else:
    environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
paypal_client = PayPalHttpClient(environment)

class PaymentService:
    @staticmethod
    async def create_paypal_order(user: User, amount: float, currency: str = "USD", plan_id: str = "Pro", db: AsyncSession = None):
        request = OrdersCreateRequest()
        request.prefer('return=representation')
        request.request_body({
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "custom_id": f"{user.id}|{plan_id}"
            }]
        })

        try:
            response = paypal_client.execute(request)
            order_id = response.result.id

            if db:
                payment = Payment(
                    user_id=user.id,
                    provider="paypal",
                    transaction_id=order_id,
                    amount=amount,
                    currency=currency,
                    status=PaymentStatus.PENDING,
                    plan_id=plan_id
                )
                db.add(payment)
                await db.commit()
                
            return {"id": order_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def handle_paypal_capture(order_id: str, db: AsyncSession):
        # 1. Capture the order in PayPal
        request = OrdersCaptureRequest(order_id)
        try:
            response = paypal_client.execute(request)
            order = response.result
            
            # 2. Check if capture was successful
            if order.status == "COMPLETED":
                # Extract metadata from the purchase unit (stored during create_order)
                # Note: Capture response includes purchase_units
                custom_id = order.purchase_units[0].payments.captures[0].custom_id if hasattr(order.purchase_units[0].payments, 'captures') else None
                
                # If custom_id is not in capture, we try to get it from the order itself (as defined in create_order)
                if not custom_id:
                    # In some SDK versions/flows, we might need to get the order details again if custom_id isn't in capture result
                    get_request = OrdersGetRequest(order_id)
                    get_resp = paypal_client.execute(get_request)
                    custom_id = get_resp.result.purchase_units[0].custom_id

                if custom_id:
                    user_id_str, plan_id = custom_id.split("|")
                    user_id = int(user_id_str)
                    await PaymentService._fulfill_payment(db, "paypal", order_id, user_id, plan_id)
                    return {"status": "success"}
                else:
                    raise HTTPException(status_code=400, detail="Metadata (custom_id) not found in order")
            else:
                 raise HTTPException(status_code=400, detail=f"Order status: {order.status}")
        except Exception as e:
             print(f"PayPal Capture Error: {str(e)}")
             raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def _fulfill_payment(db: AsyncSession, provider: str, transaction_id: str, user_id: int, plan_id: str):
        # 1. Update Payment Record
        result = await db.execute(select(Payment).where(Payment.transaction_id == transaction_id))
        payment = result.scalars().first()
        
        if not payment:
            # Fallback if payment wasn't created in create order step (unlikely but possible)
            # Fetch user to ensure valid
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalars().first()
            if not user:
                 print(f"User {user_id} not found for payment fulfillment")
                 return

            # Note: We don't have amount here easily without querying provider again, but assuming logic holds for update
            payment = Payment(user_id=user_id, provider=provider, transaction_id=transaction_id, status=PaymentStatus.COMPLETED, plan_id=plan_id, amount=0) # Amount 0 placeholder if missing
            db.add(payment)
        else:
            payment.status = PaymentStatus.COMPLETED
        
        # 2. Update User (Unlock Premium)
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if user:
            user.is_premium = True
            user.premium_plan_id = plan_id
            
            # Set subscription dates
            now = datetime.now()
            user.last_billing_reset = now
            user.subscription_end_date = now + timedelta(days=30)
            
            # Reset counts for the new billing cycle
            user.monthly_conversion_count = 0
            # user.free_conversion_count = 0  # We keep this as total history if needed, but not for limits
        
        await db.commit()
