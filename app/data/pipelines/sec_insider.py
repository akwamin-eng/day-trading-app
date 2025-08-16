# app/data/pipelines/sec_insider.py

"""
SEC EDGAR Insider Trading Pipeline
Fetches Form 4 filings (insider trades) from https://data.sec.gov/submissions/CIKXXXX.json
No API key needed — just a valid User-Agent header.
"""

import requests
import logging
import json
from datetime import datetime
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

# Required: SEC requires a realistic User-Agent to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
    "Connection": "keep-alive",
}

# List of top companies to monitor (Ticker: CIK)
COMPANY_CIKS = {
    "AAPL": "0000320193",  # Apple
    "MSFT": "0000789019",  # Microsoft
    "GOOGL": "0001652044", # Alphabet
    "TSLA": "0001318605",  # Tesla
    "AMZN": "0001018724",  # Amazon
    "META": "0001326801",  # Meta
    "NVDA": "0001045810",  # NVIDIA
    "JPM": "0000019617",   # JPMorgan
    "XOM": "0000034088",   # Exxon
    "BRK.B": "0001067983"  # Berkshire Hathaway
}

def fetch_insider_trades(cik: str, ticker: str):
    """
    Fetch insider trades for a company using its CIK.
    Parses transactionReports from CIK.json.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    logging.info(f"🔍 Fetching insider trades for {ticker} (CIK: {cik})")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 404:
            logging.warning(f"⚠️ CIK {cik} not found (404). Check formatting.")
            return []
        elif resp.status_code == 403:
            logging.error("❌ 403 Forbidden: SEC is blocking your request. Check User-Agent.")
            return []
        elif resp.status_code != 200:
            logging.error(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return []

        # Check if we got the real data or a placeholder
        if "For best practices on efficiently downloading information from SEC.gov" in resp.text:
            logging.error("❌ SEC is blocking you. You're seeing the 'best practices' page.")
            logging.error("💡 Try: using a real User-Agent, running from Cloud Run, or adding delay.")
            return []

        data = resp.json()
        filings = data.get("transactionReports", [])
        
        if not filings:
            logging.info(f"ℹ️ No Form 4 filings found for {ticker}")
            return []

        trades = []
        for filing in filings:
            try:
                # Extract key fields
                trade = {
                    "company": ticker,
                    "insider_name": filing.get("reportingOwnerName", "Unknown"),
                    "relationship": filing.get("reportingOwnerRelationship", "Unknown"),
                    "transaction_type": filing.get("transactionType", "Unknown"),
                    "acquired_disposed": filing.get("acquiredDisposedCode", "A/D"),
                    "shares": filing.get("amountOfShares", "Unknown"),
                    "price_per_share": filing.get("pricePerShare", "Unknown"),
                    "securities_owned": filing.get("securitiesOwned", "Unknown"),
                    "filing_date": filing.get("filingDate"),
                    "accession_number": filing.get("accessionNumber"),
                    "link_to_filing": f"https://www.sec.gov/Archives/edgar/data/{cik}/{filing['accessionNumber'].replace('-', '')}/",
                    "source": "sec_edgar_form4",
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                trades.append(trade)
            except Exception as e:
                logging.error(f"❌ Failed to parse filing: {e}")
                continue

        logging.info(f"✅ Fetched {len(trades)} insider trade(s) for {ticker}")
        return trades

    except requests.exceptions.Timeout:
        logging.error(f"❌ Request timed out for {ticker}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Request failed for {ticker}: {e}")
        return []
    except Exception as e:
        logging.error(f"❌ Unexpected error for {ticker}: {e}")
        return []


# === Main Execution ===
if __name__ == "__main__":
    print("🧪 Testing SEC EDGAR Insider Pipeline...")
    os.makedirs("data/outputs", exist_ok=True)
    
    all_trades = []
    for ticker, cik in COMPANY_CIKS.items():
        trades = fetch_insider_trades(cik, ticker)
        all_trades.extend(trades)
        time.sleep(1.5)  # Be respectful — SEC rate limits
    
    output_file = "data/outputs/sec_insider.json"
    with open(output_file, "w") as f:
        json.dump(all_trades, f, indent=2)
    print(f"💾 Saved {len(all_trades)} insider trade(s) to {output_file}")
