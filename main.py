import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
PUMPFUN_AMM_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P6")
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
# ==================


async def fetch_vaults():
    client = AsyncClient(RPC_URL)
    print(f"🔍 Scanning Pump.fun AMM program for vaults linked to mint {TOKEN_MINT}...\n")

    try:
        # Get all accounts under the Pump.fun AMM program
        response = await client.get_program_accounts(PUMPFUN_AMM_PROGRAM)
        accounts = response.get("result", [])

        found_accounts = []
        for acc in accounts:
            data = acc["account"]["data"][0]
            # Convert base64 to bytes
            from base64 import b64decode
            decoded = b64decode(data)

            if TOKEN_MINT.encode("utf-8") in decoded:
                found_accounts.append(acc["pubkey"])

        if not found_accounts:
            print("⚠️ No vaults found for this token. It may have graduated or uses a custom pool.")
        else:
            print("✅ Vault-related accounts found:")
            for v in found_accounts:
                print(f" - {v}")

    except Exception as e:
        print(f"❌ Vault fetch error: {e}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(fetch_vaults())