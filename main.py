import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P6")
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
# ==================


async def auto_vaults(client: AsyncClient, token_mint: str):
    """Auto-detect vaults and LP mint for a Pump.fun token"""
    print(f"🔍 Finding vaults for token mint: {token_mint} ...")
    try:
        mint_pubkey = Pubkey.from_string(token_mint)
        resp = await client.get_program_accounts(
            PUMPFUN_AMM_PROGRAM,
            encoding="jsonParsed",
            filters=[{"memcmp": {"offset": 0, "bytes": str(mint_pubkey)}}]
        )

        # ✅ Access data properly (resp.value, not resp.get())
        if not resp.value or len(resp.value) == 0:
            print("⚠️ No vaults found for this mint.")
            return None

        pool = resp.value[0]
        data = pool.account.data

        # Defensive parse
        if isinstance(data, dict) and "parsed" in data:
            info = data["parsed"]["info"]
            base_vault = info.get("baseVault")
            quote_vault = info.get("quoteVault")
        else:
            print("⚠️ Unexpected data structure. Can't parse vaults.")
            return None

        print("✅ Vaults found:")
        print(f"Base Vault: {base_vault}")
        print(f"Quote Vault: {quote_vault}")
        return base_vault, quote_vault

    except Exception as e:
        print(f"❌ Vault fetch error: {e}")
        return None