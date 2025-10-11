# main.py
# Pump.fun Sniper Bot Read-Only Tracker (better numeric formatting)
# Compatible with solana==0.30.2 and solders==0.18.1
# Run: python main.py

import asyncio
import time
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"

TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
BASE_VAULT = "4KyZRpPvSzta1A375xsS53L8hosAqqQHhxKKB46dTb3G"   # Jewcoin
QUOTE_VAULT = "4DRQKmRNj8W2hexGe5r44H3uEodvfAJKQaFn1SDvh3gr"  # WSOL

WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6

UPDATE_INTERVAL = 600  # seconds = 10 minutes
# ==================


def format_value(v: float,
                 min_fixed_decimals: int = 6,
                 max_fixed_decimals: int = 12,
                 sci_threshold: float = 1e-12) -> str:
    """
    Smart numeric formatter:
      - If v == 0 -> "0"
      - If abs(v) >= 10**-min_fixed_decimals -> show fixed-point with up to max_fixed_decimals
      - If smaller than that but >= sci_threshold -> show fixed with max_fixed_decimals
      - If smaller than sci_threshold -> show scientific with 6 significant digits
    Ensures non-zero tiny values never display as "0.000".
    """
    if v == 0 or v is None:
        return "0"
    av = abs(v)

    # If value is reasonably large, use fewer decimals
    if av >= 10 ** (-min_fixed_decimals):
        # Adapt decimal places to magnitude but keep between min and max
        # e.g., for big numbers show min_fixed_decimals, for tiny show more
        # compute decimals roughly:
        decimals = min(max_fixed_decimals, max(min_fixed_decimals, int(-1 * ( (len(str(int(av))) ) ) ) + min_fixed_decimals))
        # fallback: just use min_fixed_decimals
        decimals = min_fixed_decimals if decimals <= 0 else decimals
        fmt = f"{{:.{decimals}f}}"
        return fmt.format(v)
    # If very small but not tiny enough for sci, show max_fixed_decimals
    if av >= sci_threshold:
        fmt = f"{{:.{max_fixed_decimals}f}}"
        return fmt.format(v)
    # Very tiny -> scientific
    return f"{v:.6e}"


async def get_balance(client: AsyncClient, vault: str):
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(vault))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"❌ Error fetching balance for {vault}: {e}")
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception as e:
        print(f"❌ Error fetching token supply: {e}")
        return 0, 0


async def fetch_pool_info():
    client = AsyncClient(RPC_URL)
    try:
        # Vault balances
        base_amt, base_dec = await get_balance(client, BASE_VAULT)
        quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

        base = base_amt / (10 ** base_dec) if base_dec else 0
        quote = quote_amt / (10 ** quote_dec) if quote_dec else 0
        price = quote / base if base > 0 else 0.0
        lp = base * price + quote

        # Supply & Market Cap
        supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
        supply_norm = supply / (10 ** sup_dec) if sup_dec else 0
        mcap = price * supply_norm

        # Nicely formatted output (never prints 0.000 for tiny non-zero values)
        print(f"\n===== Pump.fun Pool Info @ {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
        print(f"Base Vault: {BASE_VAULT} ({format_value(base, min_fixed_decimals=4, max_fixed_decimals=10)} tokens)")
        print(f"Quote Vault: {QUOTE_VAULT} ({format_value(quote, min_fixed_decimals=6, max_fixed_decimals=10)} WSOL)")
        print(f"💰 Price (WSOL): {format_value(price, min_fixed_decimals=8, max_fixed_decimals=14)}")
        print(f"💧 Liquidity (LP WSOL): {format_value(lp, min_fixed_decimals=4, max_fixed_decimals=8)}")
        print(f"📊 Supply: {format_value(supply_norm, min_fixed_decimals=2, max_fixed_decimals=6)}")
        print(f"🏦 Market Cap (WSOL): {format_value(mcap, min_fixed_decimals=2, max_fixed_decimals=6)}")
        print("========================================================")
    finally:
        await client.close()


async def main_loop():
    while True:
        await fetch_pool_info()
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main_loop())