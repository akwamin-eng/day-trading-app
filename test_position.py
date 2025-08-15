# test_position.py

from app.risk.position import get_position_size
from app.utils.secrets import get_paper_api_key, get_paper_secret_key

api_key = get_paper_api_key()
secret_key = get_paper_secret_key()
price = 175.35  # Mock price

qty = get_position_size('AAPL', api_key, secret_key)
print(f'📊 Position: {qty} shares')
print(f'📉 Stop-Loss: ${round(175.35 * 0.98, 2)}')
print(f'📈 Take-Profit: ${round(175.35 * 1.04, 2)}')
