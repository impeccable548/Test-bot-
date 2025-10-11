# main.py
# Auto Vault Fetch + Token Data Tracker for Pump.fun tokens on Solana
# Run: python main.py

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"  # Replace with your token mint
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("9vgRf6Ryz5pEbWohMFWnp6mri5XK7kqhM7ssD3VxZZpY")  # ✅ official pump.fun AMM program

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6  # adjust based on your token
# ==================


async def auto_vaults(client: AsyncClient, token_mint: str):
    """Auto-detect vaults and LP mint for a Pump.fun token"""
    print(f"🔍 Finding vaults for token mint: {token_mint} ...")
    try:
        mint_pubkey = Pubkey.from_string(token_mint)

        # Important fix: convert pubkey to base58 string properly for filters
        filters = [
            MemcmpOpts(offset=0, bytes=mint_pubkey.to_base58().decode("utf-8"))
        ]

        resp = await client.get_program_accounts(
            PUMPFUN_AMM_PROGRAM,
            encoding="jsonParsed",
            opts={"filters": filters}
        )

        if not resp.value:
            print("⚠️ No vaults found for this mint.")
            return None

        pool = resp.value[0]
        data = pool.account.data
        parsed_info = data["parsed"]["info"]

        base_vault = parsed_info["baseVault"]
        quote_vault = parsed_info["quoteVault"]

        print("✅ Vaults found:")
        print(f"Base Vault: {base_vault}")
        print(f"Quote Vault: {quote_vault}")
        return base_vault, quote_vault

    except Exception as e:
        print(f"❌ Vault fetch error: {e}")
        return None


async def get_balance(client: AsyncClient, account: str):
    """Fetch SPL token account balance"""
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account))
        val = resp.get("result", {}).get("value")
        if not val:
            return 0, 0
        return int(val["amount"]), int(val["decimals"])
    except Exception as e:
        print(f"⚠️ Balance fetch failed: {e}")
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch token supply"""
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = resp.get("result", {}).get("value")
        if not val:
            return 0, 0
        return int(val["amount"]), int(val["decimals"])
    except Exception as e:
        print(f"⚠️ Supply fetch failed: {e}")
        return 0, 0


async def main():
    client = AsyncClient(RPC_URL)
    vaults = await auto_vaults(client, TOKEN_MINT)

    if not vaults:
        await client.close()
        return

    BASE_VAULT, QUOTE_VAULT = vaults

    # Get balances
    base_amt, base_dec = await get_balance(client, BASE_VAULT)
    quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

    # Normalize balances
    base = base_amt / (10 ** base_dec) if base_dec else 0
    quote = quote_amt / (10 ** quote_dec) if quote_dec else 0

    print(f"\nBase Vault (Token): {base}")
    print(f"Quote Vault (WSOL): {quote}")

    # Calculate price
    price = quote / base if base > 0 else 0
    print(f"💰 Price (in WSOL): {price}")

    # Supply + Market Cap
    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec) if sup_dec else 0
    mcap = price * supply_norm

    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")

    print("-" * 40)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())