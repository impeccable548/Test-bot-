# main.py
# Pump.fun Pool Info SDK (auto raw byte inspection)
# Compatible with solana==0.30.2 and solders==0.18.1

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6

POOL_ACCOUNT = "9zgLmaVCxc7u6ZHG8HMSau6AUjRq8pnM8KL4eDJDYjU9"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"

# Replace with actual vaults
BASE_VAULT = "HG7q9f1k61ZRXvtX3ywVXVJK3zWhnGwg3TJCu74eyWFv"
QUOTE_VAULT = "4CCPPGq4bvhMtTqWkXF9iuQGNx1bKDdjBytHi769hJto"

# Tentative offsets (will be updated after inspection)
BASE_VAULT_OFFSET = (64, 72)  # default, likely wrong
QUOTE_VAULT_OFFSET = (64, 72)  # default, likely wrong


async def print_raw_bytes(account_pubkey: str, length: int = 128):
    """Print first `length` bytes of an account for inspection"""
    client = AsyncClient(RPC_URL)
    resp = await client.get_account_info(Pubkey.from_string(account_pubkey))
    await client.close()
    if not resp.value:
        print(f"❌ Account {account_pubkey} not found.")
        return
    data = resp.value.data
    print(f"Raw bytes for {account_pubkey}: {data[:length]}")


async def get_token_balance(client: AsyncClient, vault: str, start: int, end: int):
    """Fetch SPL token balance directly from account using custom byte slice"""
    try:
        resp = await client.get_account_info(Pubkey.from_string(vault))
        if not resp.value:
            return 0
        data = resp.value.data
        amount_bytes = data[start:end]
        return int.from_bytes(amount_bytes, "little")
    except Exception as e:
        print(f"❌ Error fetching balance for {vault}: {e}")
        return 0


async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch total token supply directly from mint account"""
    try:
        resp = await client.get_account_info(Pubkey.from_string(mint))
        if not resp.value:
            return 0
        data = resp.value.data
        amount_bytes = data[36:44]  # SPL standard
        return int.from_bytes(amount_bytes, "little")
    except Exception as e:
        print(f"❌ Error fetching supply: {e}")
        return 0


async def fetch_pool_info():
    client = AsyncClient(RPC_URL)
    
    # 👀 Uncomment these lines first to inspect raw vault bytes
    # await print_raw_bytes(BASE_VAULT)
    # await print_raw_bytes(QUOTE_VAULT)

    # After inspecting raw bytes, update offsets
    base_amt = await get_token_balance(client, BASE_VAULT, *BASE_VAULT_OFFSET)
    quote_amt = await get_token_balance(client, QUOTE_VAULT, *QUOTE_VAULT_OFFSET)

    base = base_amt / (10 ** TOKEN_DECIMALS)
    quote = quote_amt / (10 ** WSOL_DECIMALS)
    price = quote / base if base > 0 else 0
    lp = base * price + quote

    supply = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** TOKEN_DECIMALS)
    mcap = price * supply_norm

    await client.close()

    print("===== Pump.fun Pool Info =====")
    print(f"Pool Account: {POOL_ACCOUNT}")
    print(f"Base Vault: {BASE_VAULT} ({base} tokens)")
    print(f"Quote Vault: {QUOTE_VAULT} ({quote} WSOL)")
    print(f"Price (in WSOL): {price}")
    print(f"Liquidity (LP in WSOL): {lp}")
    print(f"Supply: {supply_norm}")
    print(f"Market Cap (WSOL): {mcap}")
    print("==============================")

if __name__ == "__main__":
    asyncio.run(fetch_pool_info())