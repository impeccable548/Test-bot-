# main.py
# Pump.fun Pool Tracker with Volume
# Run: python main.py

import asyncio
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"

TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
BASE_VAULT = "HG7q9f1k61ZRXvtX3ywVXVJK3zWhnGwg3TJCu74eyWFv"
QUOTE_VAULT = "4CCPPGq4bvhMtTqWkXF9iuQGNx1bKDdjBytHi769hJto"

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6

POLL_INTERVAL = 30  # seconds
# ==================

async def get_balance(client: AsyncClient, account: str):
    resp = await client.get_token_account_balance(PublicKey(account))
    val = resp.get("result", {}).get("value")
    if not val:
        return 0
    return int(val["amount"]), int(val["decimals"])

async def get_token_supply(client: AsyncClient, mint: str):
    resp = await client.get_token_supply(PublicKey(mint))
    val = resp.get("result", {}).get("value")
    if not val:
        return 0, 0
    return int(val["amount"]), int(val["decimals"])

async def fetch_pool_info(client):
    base_amt, base_dec = await get_balance(client, BASE_VAULT)
    quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)
    base = base_amt / (10 ** base_dec)
    quote = quote_amt / (10 ** quote_dec)

    price = quote / base if base > 0 else 0

    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec)
    mcap = price * supply_norm

    lp = base * price + quote

    return base, quote, price, supply_norm, mcap, lp

async def track_volume():
    client = AsyncClient(RPC_URL)
    prev_base, prev_quote, _, _, _, _ = await fetch_pool_info(client)
    print("Starting Pump.fun Tracker with Volume...")
    
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        base, quote, price, supply, mcap, lp = await fetch_pool_info(client)

        # Calculate volume in this interval
        delta_base = abs(base - prev_base)
        delta_quote = abs(quote - prev_quote)
        volume_wsol = delta_quote + delta_base * price

        print("==============================")
        print(f"Base Vault: {base} tokens")
        print(f"Quote Vault: {quote} WSOL")
        print(f"💰 Price (WSOL): {price}")
        print(f"📊 Supply: {supply}")
        print(f"🏦 Market Cap: {mcap}")
        print(f"💧 LP (WSOL): {lp}")
        print(f"📈 Volume last {POLL_INTERVAL}s (WSOL): {volume_wsol}")
        print("==============================")

        prev_base, prev_quote = base, quote

    await client.close()

if __name__ == "__main__":
    asyncio.run(track_volume())