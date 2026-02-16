from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.core.security import get_current_user
from app.models.user import User
from app.services.payment_service import PaymentService
from pydantic import BaseModel

router = APIRouter(tags=["payments"])

class KeyRequest(BaseModel):
    pass

class CreatePayPalOrderRequest(BaseModel):
    amount: float
    currency: str = "USD"
    plan_id: str

class PayPalCaptureRequest(BaseModel):
    orderID: str

@router.post("/create-paypal-order")
async def create_paypal_order(
    request: CreatePayPalOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await PaymentService.create_paypal_order(user, request.amount, request.currency, request.plan_id, db)

@router.post("/capture-paypal-order")
async def capture_paypal_order(
    request: PayPalCaptureRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Actually capture is done by frontend usually with paypal buttons, but we need to verify/record it
    # OR if using 'AUTHORIZE' intent, we capture here. 
    # With 'CAPTURE' intent in create_order, the frontend logic calls onApprove > actions.order.capture()
    # Then calls this backend endpoint to record/verify.
    
    # We will assume frontend captures and just reports success, BUT for security we should verify status.
    return await PaymentService.handle_paypal_capture(request.orderID, db)
