from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient

# Use paper trading
API_KEY = "PKULBHVQE87MGAYSSN4U"
SECRET_KEY = "pUSLSYh0PzdGc0bIGxoDrDEaoqtfq05JV5ezDxHG"

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
account = trading_client.get_account()
print(account.status)

