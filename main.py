# main.py
# Pump.fun Token Tracker SDK (API Edition)
# Simplified version — no RPC stress, instant vault + price data

import requests
import time

# ===== CONFIG =====
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
API_URL = f"https://frontend-api.pump.fun/coins/{TOKEN_MINT}"
REFRESH_INTERVAL = 30  # seconds
# ==================


def fetch_token_data():
    """Fetch token and vault data from Pump.fun API"""
    try:
        resp = requests.get(API_URL, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ API returned status {resp.status_code}")
            return None

        data = resp.json()
        return data

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None


def display_token_info(data):
    """Display formatted token and market info"""
    print("\n🚀 Pump.fun Token Data")
    print("-" * 40)

    name = data.get("name", "Unknown")
    symbol = data.get("symbol", "")
    complete = data.get("complete", False)
    bonding_curve = data.get("bonding_curve", "N/A")
    vaults = data.get("vaults", {})

    base_vault = vaults.get("baseVault", "N/A")
    quote_vault = vaults.get("quoteVault", "N/A")

    sol_reserve = float(data.get("virtual_sol_reserves", 0))
    token_reserve = float(data.get("virtual_token_reserves", 0))
    price = sol_reserve / token_reserve if token_reserve > 0 else 0
    mcap = float(data.get("market_cap", 0))

    print(f"🪙 Token: {name} ({symbol})")
    print(f"💰 Price (SOL): {price:.9f}")
    print(f"🏦 Market Cap (USD est.): ${mcap:,.2f}")
    print(f"📦 Bonding Curve: {bonding_curve}")
    print(f"🧱 Base Vault: {base_vault}")
    print(f"💧 Quote Vault: {quote_vault}")
    print(f"✅ Graduated: {'Yes' if complete else 'No'}")
    print("-" * 40)


def main():
    print("🌐 Pump.fun Token Tracker SDK initialized...\n")

    while True:
        data = fetch_token_data()
        if data:
            display_token_info(data)
        else:
            print("⚠️ Failed to fetch token data.")

        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()