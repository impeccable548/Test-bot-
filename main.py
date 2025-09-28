# main.py
# PumpFun Token Tracker - Read-only Solana bot
# Run locally: python main.py
# Deploy on Render: Background Worker

import asyncio
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"

# Token mint
TOKEN_MINT = "BqndqeBCNSEftBKmbTbLVx1RX5zd5J3AGL9sG55Jpump"

# Vaults
BASE_VAULT = "AwJ8XtG2rgmrxhqeBG55voCT2LxBB3iQzs9DKtrzUHRd"   # Q4
QUOTE_VAULT = "3HzVMQo6pboZB7bDuDeJg18wsZJWT4chnZV3y2BJwFQQ"  # WSOL
# ==================


async def get_balance(client: AsyncClient, account: str):
    resp = await client.get_token_account_balance(PublicKey(account))
    val = resp.get("result", {}).get("value")
    if not val:
        return 0, 0
    return int(val["amount"]), int(val["decimals"])


async def get_token_supply(client: AsyncClient, mint: str):
    resp = await client.get_token_supply(PublicKey(mint))
    val = resp.get("result", {}).get("value")
    if not val:
        return 0, 0
    return int(val["amount"]), int(val["decimals"])


async def main():
    client = AsyncClient(RPC_URL)

    # Get balances
    base_amt, base_dec = await get_balance(client, BASE_VAULT)
    quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

    base = base_amt / (10 ** base_dec)
    quote = quote_amt / (10 ** quote_dec)

    print(f"Base Vault (token): {base}")
    print(f"Quote Vault (WSOL): {quote}")

    # Price
    price = quote / base if base > 0 else 0
    print(f"\n💰 Price (in WSOL): {price}")

    # Supply + Market Cap
    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec)
    mcap = price * supply_norm

    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")

    await client.close()


if __name__ == "__main__":
    async def loop_main():
        while True:
            try:
                await main()
            except Exception as e:
                print(f"⚠️ Error: {e}")
            print("-" * 40)
            await asyncio.sleep(30)  # run every 30s

    asyncio.run(loop_main())