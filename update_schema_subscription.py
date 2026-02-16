import asyncio
import sqlite3
from pathlib import Path

async def update_schema():
    db_path = Path("backend/sql_app.db")
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add monthly_conversion_count
        cursor.execute("ALTER TABLE users ADD COLUMN monthly_conversion_count INTEGER DEFAULT 0")
        print("Added monthly_conversion_count column")
    except sqlite3.OperationalError as e:
        print(f"Error adding monthly_conversion_count: {e}")

    try:
        # Add last_billing_reset
        cursor.execute("ALTER TABLE users ADD COLUMN last_billing_reset DATETIME")
        print("Added last_billing_reset column")
    except sqlite3.OperationalError as e:
        print(f"Error adding last_billing_reset: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    asyncio.run(update_schema())
