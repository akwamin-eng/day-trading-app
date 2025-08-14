k# main.py

"""
Main launcher for the trading app.
Respects market hours and starts ingestion when market opens.
"""

import asyncio
from datetime import datetime

# Local modules
from app.utils.market_hours import is_market_open, wait_until_market_open
from app.data.ingest import main as run_ingestion


async def launch_trading_app():
    print(f"🎯 Trading app started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        if is_market_open():
            print("🟢 MARKET IS OPEN — Starting data ingestion...")
            try:
                await run_ingestion()
            except Exception as e:
                print(f"❌ Error during ingestion: {e}")
        else:
            print(f"🌙 {datetime.now().strftime('%H:%M:%S')} — Market closed. Waiting...")
            await wait_until_market_open()


if __name__ == "__main__":
    asyncio.run(launch_trading_app())
