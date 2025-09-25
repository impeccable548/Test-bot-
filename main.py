# main.py
# Test Bot - Read-only tracker for a PumpFun token on Solana.
# Run: python main.py

import asyncio
import base64
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
# Token mint (the token you want to track)
TOKEN_MINT = "CKVZPWFPaJArEaPnk16CXpFtFXjuCxCh95vBcS3Ppump"

# ✅ PumpFun platform program ID
PUMPFUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# cap scanning so RPC won’t block you
MAX_SCAN = 1000
# ==================


async def get_token_supply(client: AsyncClient, mint: PublicKey):
    resp = await client.get_token_supply(mint, commitment="confirmed")
    val = resp.get("result", {}).get("value")
    if not val:
        return None, None
    return int(val["amount"]), int(val["decimals"])


async def get_holders(client: AsyncClient, mint: PublicKey):
    resp = await client.get_token_accounts_by_mint(
        mint, encoding="jsonParsed", commitment="confirmed"
    )
    accounts = resp.get("result", {}).get("value", [])
    holders = 0
    for acc in accounts:
        amt = int(
            acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
        )
        if amt > 0:
            holders += 1
    return holders, len(accounts)


async def find_pools(client: AsyncClient, mint: PublicKey, program_id: PublicKey):
    resp = await client.get_program_accounts(
        program_id, encoding="base64", commitment="confirmed"
    )
    accounts = resp.get("result", [])
    print(f"Scanned {len(accounts)} program accounts (showing up to {MAX_SCAN})")

    candidates = []
    mint_bytes = bytes(mint)

    for idx, acc in enumerate(accounts[:MAX_SCAN]):
        raw = base64.b64decode(acc["account"]["data"][0])
        if mint_bytes in raw:
            candidates.append(acc["pubkey"])

    return candidates


async def main():
    client = AsyncClient(RPC_URL)
    mint_pk = PublicKey(TOKEN_MINT)
    prog_pk = PublicKey(PUMPFUN_PROGRAM_ID)

    print("🔗 Connecting to RPC:", RPC_URL)
    print("🎯 Token Mint:", TOKEN_MINT)
    print("🏗  PumpFun Program ID:", PUMPFUN_PROGRAM_ID)

    supply, decimals = await get_token_supply(client, mint_pk)
    print(f"\n📊 Supply: {supply} (decimals={decimals})")

    holders, total = await get_holders(client, mint_pk)
    print(f"👥 Holders: {holders} / {total} accounts")

    pools = await find_pools(client, mint_pk, prog_pk)
    if pools:
        print(f"\n💧 Candidate pool accounts linked to {TOKEN_MINT}:")
        for p in pools:
            print(" -", p)
    else:
        print("\n⚠️ No pools found (check program ID or RPC limits).")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())