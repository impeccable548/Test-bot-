# main.py
# Pump.fun Token Tracker - solders SDK (Solana)
# Run: python main.py

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"

# Token mint
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"

# Vaults
BASE_VAULT = "4KyZRpPvSzta1A375xsS53L8hosAqqQHhxKKB46dTb3G"   # JewCoin
QUOTE_VAULT = "4DRQKmRNj8W2hexGe5r44H3uEodvfAJKQaFn1SDvh3gr"  # WSOL

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6
# ==================


async def get_balance(client: AsyncClient, account: str):
    """Fetch SPL token balance for an account"""
    resp = await client.get_token_account_balance(Pubkey.from_string(account))
    val = getattr(resp, "value", None)
    if not val:
        return 0, 0
    return int(val.amount), int(val.decimals)


async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch total supply of token"""
    resp = await client.get_token_supply(Pubkey.from_string(mint))
    val = getattr(resp, "value", None)
    if not val:
        return 0, 0
    return int(val.amount), int(val.decimals)


async def main():
    client = AsyncClient(RPC_URL)

    # Get balances
    base_amt, base_dec = await get_balance(client, BASE_VAULT)
    quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

    # Normalize
    base = base_amt / (10 ** base_dec)
    quote = quote_amt / (10 ** quote_dec)

    print(f"Base Vault (token): {base}")
    print(f"Quote Vault (WSOL): {quote}")

    # Price
    price = quote / base if base > 0 else 0
    print(f"\n💰 Price (in WSOL): {price}")

    # Liquidity
    lp = base * price + quote
    print(f"💧 Liquidity (LP in WSOL): {lp}")

    # Supply + market cap
    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec)
    mcap = price * supply_norm

    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())