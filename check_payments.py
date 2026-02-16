import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.payment import Payment
from app.models.user import User

async def check_payments():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Payment, User).join(User, Payment.user_id == User.id))
        payments = res.all()
        print(f"Total payments found: {len(payments)}")
        for p, u in payments:
            print(f"--- Payment ID: {p.id} ---")
            print(f"User: {u.email}")
            print(f"Plan: {p.plan_id}")
            print(f"Amount: {p.amount} {p.currency}")
            print(f"Status: {p.status}")
            print(f"PayPal ID: {p.transaction_id}")
            print(f"Created At: {p.created_at}")

if __name__ == "__main__":
    asyncio.run(check_payments())
