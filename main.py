# main.py
# Auto Vault Fetch + Token Data Tracker for Pump.fun (Solana)
# Uses solana==0.30.2 + solders==0.18.1

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts
import base58

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

# ==================

async def auto_vaults(client: AsyncClient, token_mint: str):
    print(f"🔍 Detecting vaults for token mint: {token_mint}")
    try:
        mint_pub = Pubkey.from_string(token_mint)
        # convert pubkey bytes → base58 string for filter
        mint_b58 = base58.b58encode(mint_pub.__bytes__()).decode("utf-8")

        resp = await client.get_program_accounts(
            PUMPFUN_AMM_PROGRAM,
            encoding="jsonParsed",
            filters=[MemcmpOpts(offset=0, bytes=mint_b58)]
        )

        val = getattr(resp, "value", None)
        if not val or len(val) == 0:
            print("⚠️ No vaults found.")
            return None

        pool = val[0]
        info = pool.account.data["parsed"]["info"]
        base_vault = info.get("baseVault")
        quote_vault = info.get("quoteVault")

        print(f"✅ Vaults: base={base_vault}, quote={quote_vault}")
        return base_vault, quote_vault

    except Exception as e:
        print(f"❌ Vault fetch error: {e}")
        return None

async def get_balance(client: AsyncClient, acct: str):
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(acct))
        val = resp.value
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"⚠️ Balance fetch error for {acct}: {e}")
        return 0, 0

async def get_token_supply(client: AsyncClient, mint: str):
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = resp.value
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"⚠️ Supply fetch error for {mint}: {e}")
        return 0, 0

async def main():
    client = AsyncClient(RPC_URL)
    vaults = await auto_vaults(client, TOKEN_MINT)

    if not vaults:
        await client.close()
        return

    base_vault, quote_vault = vaults
    base_amt, base_dec = await get_balance(client, base_vault)
    quote_amt, quote_dec = await get_balance(client, quote_vault)

    base = base_amt / (10 ** base_dec) if base_dec else 0
    quote = quote_amt / (10 ** quote_dec) if quote_dec else 0

    print(f"Base Vault Token: {base}")
    print(f"Quote Vault WSOL: {quote}")

    price = quote / base if base > 0 else 0
    print(f"💰 Price in WSOL: {price}")

    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec) if sup_dec else 0
    mcap = price * supply_norm
    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())