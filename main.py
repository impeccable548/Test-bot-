# main.py
# Pump.fun Auto Vault SDK — Debug & Stable Edition

import asyncio
import base58
import traceback
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts

RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

async def auto_vaults(client: AsyncClient, token_mint: str):
    print(f"🔍 Detecting vaults for token mint: {token_mint}")
    try:
        mint_pub = Pubkey.from_string(token_mint)
        mint_b58 = base58.b58encode(mint_pub.__bytes__()).decode()

        resp = await client.get_program_accounts(
            PUMPFUN_AMM_PROGRAM,
            encoding="jsonParsed",
            filters=[MemcmpOpts(offset=0, bytes=mint_b58)]
        )

        val = getattr(resp, "value", None)
        if not val:
            print("⚠️ No vaults found.")
            return None

        pool = val[0]
        data = getattr(pool.account, "data", None)
        if not data:
            print("⚠️ No account data found.")
            print(f"Raw pool: {pool}")
            return None

        # Try to extract parsed info safely
        info = None
        if isinstance(data, dict) and "parsed" in data:
            info = data["parsed"].get("info", {})
        elif isinstance(data, (list, tuple)):
            print("⚠️ Account data not parsed, dumping raw data:")
            print(data)
            return None

        if not info:
            print("⚠️ Could not find parsed vault info. Full data dump:")
            print(data)
            return None

        base_vault = info.get("baseVault")
        quote_vault = info.get("quoteVault")

        print(f"✅ Vaults found!\nBase Vault: {base_vault}\nQuote Vault: {quote_vault}")
        return base_vault, quote_vault

    except Exception as e:
        print("❌ Vault fetch error:", e)
        traceback.print_exc()
        return None


async def main():
    client = AsyncClient(RPC_URL)
    await auto_vaults(client, TOKEN_MINT)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())