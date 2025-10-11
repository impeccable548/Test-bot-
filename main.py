# main.py
# ✅ Pump.fun Vault Tracker SDK + Flask keepalive
# Works on Render with solana==0.30.2, solders==0.18.1

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts
from flask import Flask
import threading

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"

# ✅ Real Pump.fun AMM Program ID
PUMPFUN_PROGRAM = Pubkey.from_string("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpMu4vP3wX5")  

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6
# ==================


async def auto_vaults(client: AsyncClient, token_mint: str):
    """Auto-detect vaults for a Pump.fun token"""
    print(f"🔍 Detecting vaults for token mint: {token_mint}")
    try:
        mint_pubkey = Pubkey.from_string(token_mint)
        filters = [MemcmpOpts(offset=0, bytes=str(mint_pubkey))]

        resp = await client.get_program_accounts(PUMPFUN_PROGRAM, encoding="jsonParsed", filters=filters)
        value = getattr(resp, "value", None)
        if not value:
            print("⚠️ No vaults found for this mint.")
            return None

        pool = value[0]
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


async def get_balance(client: AsyncClient, account: str):
    """Fetch SPL token account balance"""
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account))
        val = resp.value
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch token supply"""
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = resp.value
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


async def run_tracker():
    """Main async tracker logic"""
    client = AsyncClient(RPC_URL)
    vaults = await auto_vaults(client, TOKEN_MINT)
    if not vaults:
        await client.close()
        return

    BASE_VAULT, QUOTE_VAULT = vaults
    base_amt, base_dec = await get_balance(client, BASE_VAULT)
    quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

    base = base_amt / (10 ** base_dec)
    quote = quote_amt / (10 ** quote_dec)
    print(f"\nBase Vault (Token): {base}")
    print(f"Quote Vault (WSOL): {quote}")

    price = quote / base if base > 0 else 0
    print(f"💰 Price (in WSOL): {price}")

    supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
    supply_norm = supply / (10 ** sup_dec)
    mcap = price * supply_norm
    print(f"📊 Supply: {supply_norm}")
    print(f"🏦 Market Cap (WSOL): {mcap}")
    print("-" * 40)
    await client.close()


def background_task():
    """Loop the tracker every few minutes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(run_tracker())
        print("⏳ Waiting 3 mins before next fetch...\n")
        import time
        time.sleep(180)


# === Flask keepalive ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 Pump.fun Vault SDK running on Render — Solana live feed active."

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    run_flask()