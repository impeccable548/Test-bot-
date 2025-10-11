# main.py
# Pump.fun Pool Info Tracker (Handles both parsed + raw data)
# Compatible with solana==0.30.2, solders==0.18.1

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
import base64
import struct

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
WSOL_DECIMALS = 9
POOL_ACCOUNT = "9zgLmaVCxc7u6ZHG8HMSau6AUjRq8pnM8KL4eDJDYjU9"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
# ==================

async def get_spl_balance(client: AsyncClient, account_pubkey: str):
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account_pubkey))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0

async def get_token_supply(client: AsyncClient, mint_pubkey: str):
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint_pubkey))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0

async def fetch_pool_info(pool_account: str, token_mint: str):
    client = AsyncClient(RPC_URL)
    try:
        pool_pubkey = Pubkey.from_string(pool_account)
        resp = await client.get_account_info(pool_pubkey, encoding="jsonParsed")

        if not resp.value:
            print("❌ Pool account not found.")
            await client.close()
            return

        data = resp.value.data

        # --- CASE 1: Parsed JSON (preferred) ---
        if isinstance(data, dict) and "parsed" in data:
            parsed = data["parsed"]["info"]
            base_vault = parsed["baseVault"]
            quote_vault = parsed["quoteVault"]

        # --- CASE 2: Raw base64 data ---
        elif isinstance(data, list) and len(data) > 0:
            raw_data = base64.b64decode(data[0])
            # Typical Pump.fun layout: first 32 bytes = baseVault, next 32 bytes = quoteVault
            base_vault = Pubkey(raw_data[0:32]).__str__()
            quote_vault = Pubkey(raw_data[32:64]).__str__()

        else:
            print("❌ Unrecognized data format.")
            await client.close()
            return

        base_amt, base_dec = await get_spl_balance(client, base_vault)
        quote_amt, quote_dec = await get_spl_balance(client, quote_vault)

        base = base_amt / (10 ** base_dec)
        quote = quote_amt / (10 ** quote_dec)
        price = quote / base if base > 0 else 0

        supply, sup_dec = await get_token_supply(client, token_mint)
        supply_norm = supply / (10 ** sup_dec)
        mcap = price * supply_norm

        await client.close()

        print("===== Pump.fun Pool Info =====")
        print(f"Pool Account: {pool_account}")
        print(f"Base Vault: {base_vault} ({base} tokens)")
        print(f"Quote Vault: {quote_vault} ({quote} WSOL)")
        print(f"Price (in WSOL): {price}")
        print(f"Supply: {supply_norm}")
        print(f"Market Cap (WSOL): {mcap}")
        print("==============================")

    except Exception as e:
        await client.close()
        print(f"❌ Error fetching pool info: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_pool_info(POOL_ACCOUNT, TOKEN_MINT))