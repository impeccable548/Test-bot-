import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("AMM55ShduEwdNoX9R4QvY7qz7f3H7T2Y9sx9X9v3x3nK")  # placeholder

# ==================


async def get_balance(client: AsyncClient, account: str):
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account))
        val = resp.get("result", {}).get("value")
        if not val:
            return 0
        return int(val["amount"]), int(val["decimals"])
    except Exception:
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = resp.get("result", {}).get("value")
        if not val:
            return 0, 0
        return int(val["amount"]), int(val["decimals"])
    except Exception:
        return 0, 0


async def auto_vaults(client: AsyncClient, token_mint: str):
    """Auto-detects vaults and LP mint for a token on Pump.fun"""
    print(f"🔍 Finding vaults for token mint: {token_mint} ...")
    try:
        mint_pubkey = Pubkey.from_string(token_mint)
        resp = await client.get_program_accounts(
            PUMPFUN_AMM_PROGRAM,
            encoding="jsonParsed",
            filters=[MemcmpOpts(offset=0, bytes=mint_pubkey.to_string())]
        )

        if not resp.value:
            print("⚠️ No vaults found for this mint.")
            return None

        pool = resp.value[0]
        data = pool.account.data
        base_vault = data["parsed"]["info"]["baseVault"]
        quote_vault = data["parsed"]["info"]["quoteVault"]

        print("✅ Vaults found:")
        print(f"Base Vault: {base_vault}")
        print(f"Quote Vault: {quote_vault}")
        return base_vault, quote_vault

    except Exception as e:
        print(f"❌ Vault fetch error: {e}")
        return None


async def main():
    client = AsyncClient(RPC_URL)
    vaults = await auto_vaults(client, TOKEN_MINT)

    if not vaults:
        print("⚠️ Could not auto-detect vaults. Exiting.")
        return

    base_vault, quote_vault = vaults

    base_amt, base_dec = await get_balance(client, base_vault)
    quote_amt, quote_dec = await get_balance(client, quote_vault)

    base = base_amt / (10 ** base_dec) if base_dec else 0
    quote = quote_amt / (10 ** quote_dec) if quote_dec else 0

    price = quote / base if base > 0 else 0

    print(f"\n💰 Price (in WSOL): {price}")

    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec)
    mcap = price * supply_norm

    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())