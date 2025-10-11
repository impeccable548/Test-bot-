import asyncio
import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts, RPCResponse
from solana.publickey import PublicKey

RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
PROGRAM_ID = PublicKey("PUMPFiN1111111111111111111111111111111111111")  # Pump.fun Program ID

async def get_vault_accounts():
    async with AsyncClient(RPC_URL) as client:
        try:
            print("🔍 Fetching vault accounts from pump.fun...")
            
            # Use proper MemcmpOpts filter
            filters = [
                MemcmpOpts(offset=0, bytes=base58.b58encode(PROGRAM_ID.__bytes__()).decode())
            ]
            
            resp: RPCResponse = await client.get_program_accounts(
                PROGRAM_ID,
                encoding="base64",
                data_size=None,
                filters=filters
            )

            if not resp or "result" not in resp.value:
                print("❌ No result in response")
                return

            accounts = resp.value["result"]
            print(f"✅ Found {len(accounts)} accounts")

            for acct in accounts[:10]:  # show first 10 to avoid overload
                pubkey = acct["pubkey"]
                print(f"Vault Account: {pubkey}")

        except Exception as e:
            print(f"❌ Vault fetch error: {e}")

async def main():
    await get_vault_accounts()

if __name__ == "__main__":
    asyncio.run(main())