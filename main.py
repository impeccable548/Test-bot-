# main.py
# Pump.fun Sniper Bot - robust tracker + tiny HTTP health server (for Web Service platforms)
# Run: python main.py
# Requirements: solana==0.30.2, solders==0.18.1

import asyncio
import time
import math
import signal
import csv
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
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
RPC_RETRIES = 3
CSV_LOG = False  # set True to append output to tracker.csv
CSV_PATH = Path("tracker.csv")
# HTTP server port (use $PORT when on render)
PORT = int(os.environ.get("PORT", "10000"))
# ==================

stop_signal = False

def handle_sigint(signum, frame):
    global stop_signal
    stop_signal = True
    print("\n⚡ Received stop signal — shutting down cleanly...")

signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)


def format_price_4sig(v: float, min_fixed_threshold: float = 1e-4, sig: int = 4, max_decimals: int = 12) -> str:
    """Format price with 4 significant digits but print as fixed decimal (no scientific notation)"""
    if v is None:
        return "N/A"
    if v == 0:
        return "0"
    if v >= min_fixed_threshold:
        # common case: show 4 decimals
        return f"{v:.4f}"
    # small values: compute decimals so we show `sig` significant digits
    exp = math.floor(math.log10(abs(v)))
    decimals = abs(exp) + (sig - 1)
    decimals = min(decimals, max_decimals)
    return f"{v:.{decimals}f}"


async def rpc_with_retry(coro_fn, *args, retries=RPC_RETRIES, delay=0.5):
    """Run coroutine with simple retry on exceptions."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return await coro_fn(*args)
        except Exception as e:
            last_exc = e
            if attempt < retries:
                await asyncio.sleep(delay * attempt)
            else:
                raise
    raise last_exc


async def get_balance(client: AsyncClient, vault: str):
    """Fetch SPL token balance with retries."""
    async def _call(v):
        return await client.get_token_account_balance(Pubkey.from_string(v))
    resp = await rpc_with_retry(_call, vault)
    val = getattr(resp, "value", None)
    if not val:
        return 0, 0
    return int(val.amount), int(val.decimals)


async def get_token_supply(client: AsyncClient, mint: str):
    async def _call(m):
        return await client.get_token_supply(Pubkey.from_string(m))
    resp = await rpc_with_retry(_call, mint)
    val = getattr(resp, "value", None)
    if not val:
        return 0, 0
    return int(val.amount), int(val.decimals)


def write_csv_row(ts_iso, base, quote, price, lp, supply, mcap):
    header = ["ts", "base", "quote", "price_wsol", "lp_wsol", "supply", "mcap_wsol"]
    exists = CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow([ts_iso, base, quote, price, lp, supply, mcap])


async def fetch_pool_info_loop():
    client = AsyncClient(RPC_URL)
    try:
        while not stop_signal:
            start_t = time.time()
            try:
                base_amt, base_dec = await get_balance(client, BASE_VAULT)
                quote_amt, quote_dec = await get_balance(client, QUOTE_VAULT)

                base = base_amt / (10 ** base_dec) if base_dec else 0.0
                quote = quote_amt / (10 ** quote_dec) if quote_dec else 0.0
                price = quote / base if base > 0 else 0.0
                lp = base * price + quote

                supply_amt, supply_dec = await get_token_supply(client, TOKEN_MINT)
                supply = supply_amt / (10 ** supply_dec) if supply_dec else 0.0
                mcap = price * supply

                ts_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                # Nicely formatted output
                print(f"\n===== Pump.fun Pool Info @ {ts_iso} =====")
                print(f"Base Vault: {BASE_VAULT} ({base:.6f} tokens)")
                print(f"Quote Vault: {QUOTE_VAULT} ({quote:.6f} WSOL)")
                print(f"💰 Price (WSOL): {format_price_4sig(price)}")
                print(f"💧 Liquidity (LP WSOL): {lp:.6f}")
                print(f"📊 Supply: {supply:,.4f}")
                print(f"🏦 Market Cap (WSOL): {mcap:,.6f}")
                print("========================================================")

                if CSV_LOG:
                    write_csv_row(ts_iso, base, quote, price, lp, supply, mcap)

            except Exception as e:
                # show error but keep loop alive
                print(f"❌ Fetch error: {e}")

            # sleep remaining interval, but exit early if stopped
            elapsed = time.time() - start_t
            to_sleep = max(0, UPDATE_INTERVAL - elapsed)
            for _ in range(int(to_sleep)):
                if stop_signal:
                    break
                await asyncio.sleep(1)
            if stop_signal:
                break

    finally:
        await client.close()
        print("🛑 Client closed, exiting.")


# ------------ tiny HTTP server for platform health checks ------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # simple OK response for healthchecks
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        # silence default HTTP logging
        return

def run_health_server():
    srv = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"🔌 Health server listening on 0.0.0.0:{PORT}")
    try:
        srv.serve_forever()
    except Exception:
        pass
    finally:
        try:
            srv.server_close()
        except Exception:
            pass

# ------------ entrypoint ------------
def main():
    # Start tiny HTTP server in background thread (so Render sees the port)
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    # Run the async fetch loop in the main thread
    try:
        asyncio.run(fetch_pool_info_loop())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()