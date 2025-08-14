# app/utils/market_hours.py

"""
Utility functions to determine if the U.S. stock market is open.
Respects trading hours and weekends.
"""

import asyncio
from datetime import datetime, time, timedelta
import pytz


# ----------------------------
# Constants
# ----------------------------

# Eastern Time zone (handles EDT/EST automatically)
ET = pytz.timezone('US/Eastern')

# Market hours (regular session)
MARKET_OPEN = time(9, 30)   # 9:30 AM ET
MARKET_CLOSE = time(16, 0)  # 4:00 PM ET


# ----------------------------
# Main Function
# ----------------------------

def is_market_open(dt=None):
    """
    Determines if the U.S. stock market is open for regular trading.

    The market is open:
      - Monday to Friday
      - 9:30 AM to 4:00 PM Eastern Time

    Args:
        dt (datetime): Optional datetime to check (naive or ET-aware).
                       Defaults to now in ET.

    Returns:
        bool: True if market is open, False otherwise.
    """
    # Use current time in ET if no datetime is provided
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        # If naive, assume it's in ET
        dt = ET.localize(dt)
    else:
        # Convert to ET if timezone-aware
        dt = dt.astimezone(ET)

    # Check if it's a weekday (Monday=0, Sunday=6)
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False

    # Extract time part for comparison
    current_time = dt.time()

    # Return True if within market hours
    return MARKET_OPEN <= current_time < MARKET_CLOSE


# ----------------------------
# Helper: Wait Until Market Open
# ----------------------------

async def wait_until_market_open():
    """
    Asynchronously wait until the next market open (9:30 AM ET).
    Intended for use in async loops (e.g., daily restart scripts).

    Yields control every 60 seconds to avoid blocking.
    """
    while not is_market_open():
        now = datetime.now(ET)
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)

        if now.weekday() >= 5:  # Weekend
            # Find next Monday
            days_ahead = 7 - now.weekday()
            next_open += timedelta(days=days_ahead)
        elif now.time() >= MARKET_OPEN:
            # Today's market has already opened — go to tomorrow
            next_open += timedelta(days=1)

        # If next_open is in the past, add one day
        if next_open <= now:
            next_open += timedelta(days=1)

        wait_seconds = (next_open - now).total_seconds()
        wait_minutes = wait_seconds / 60

        print(f"💤 Market closed. Waiting {wait_minutes:.1f} minutes until next market open (9:30 AM ET)...")
        await asyncio.sleep(min(wait_seconds, 60))  # Wake every 60 sec to recheck
