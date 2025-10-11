# main.py
# Pump.fun Pool Tracker - Solana (raw vault fetch)
# Compatible with solana==0.30.2 and solders==0.18.1
# Run: python main.py

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"

# Replace these with the actual pool vaults and token mint
BASE_VAULT = "HG7q9f1k61ZRXvtX3ywVXVJK3zWhnGwg3TJCu74eyWFv"
QUOTE_VAULT = "4CCPPGq4bvhMtTqWkXF9iuQGNx1bKDdjBytHi769hJto"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6
# ==================

async def get_balance(client: AsyncClient, vault: str):
    """Fetch SPL token balance from vault using solders"""
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(vault))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"❌ Error fetching balance for {vault}: {e}")
        return 0, 0

async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch total token supply for mint"""
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"❌ Error fetching token supply: {e}")
        return 0, 0

async def fetch_pool_info():
    client = AsyncClient(RPC_URL)
    try:
        # Get balances
        base_amt, base_dec = await get_balance(client, BASE_VAULT)
        quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

        base = base_amt / (10 ** base_dec)
        quote = quote_amt / (10 ** quote_dec)
        price = quote / base if base > 0 else 0
        lp = base * price + quote

        # Token supply
        supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
        supply_norm = supply / (10 ** sup_dec)
        mcap = price * supply_norm

        # Print results
        print("===== Pump.fun Pool Info =====")
        print(f"Base Vault: {BASE_VAULT} ({base} tokens)")
        print(f"Quote Vault: {QUOTE_VAULT} ({quote} WSOL)")
        print(f"Price (in WSOL): {price}")
        print(f"Liquidity (LP in WSOL): {lp}")
        print(f"Supply: {supply_norm}")
        print(f"Market Cap (WSOL): {mcap}")
        print("==============================")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(fetch_pool_info())