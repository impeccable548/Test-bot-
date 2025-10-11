# main.py
# On-Demand Vault & Token Tracker for Pump.fun Tokens (Solana)
# ✅ Works with solana==0.30.2 and solders==0.18.1
# ⚡ Runs only when URL is accessed — safe for Render Free Plan

import asyncio
from flask import Flask, jsonify
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"
PUMPFUN_PROGRAM = Pubkey.from_string("PUMPFiN1111111111111111111111111111111111111")  # Pump.fun AMM program
# ==================

app = Flask(__name__)


async def fetch_vaults(client: AsyncClient, token_mint: str):
    """Find vaults for Pump.fun token."""
    try:
        mint_pubkey = Pubkey.from_string(token_mint)
        resp = await client.get_program_accounts(
            PUMPFUN_PROGRAM,
            encoding="jsonParsed",
            filters=[MemcmpOpts(offset=0, bytes=str(mint_pubkey))]
        )

        value = getattr(resp, "value", None)
        if not value:
            return {"error": "No vaults found for this mint."}

        pool = value[0]
        data = pool.account.data
        base_vault = data["parsed"]["info"]["baseVault"]
        quote_vault = data["parsed"]["info"]["quoteVault"]

        return {"base_vault": base_vault, "quote_vault": quote_vault}

    except Exception as e:
        return {"error": str(e)}


async def get_balance(client: AsyncClient, account: str):
    """Fetch SPL token account balance."""
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account))
        val = resp.value
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    """Fetch token supply."""
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = resp.value
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


async def run_one_fetch():
    """Run a full one-shot data fetch for the token."""
    async with AsyncClient(RPC_URL) as client:
        vaults = await fetch_vaults(client, TOKEN_MINT)
        if "error" in vaults:
            return {"status": "error", "details": vaults["error"]}

        base_vault, quote_vault = vaults["base_vault"], vaults["quote_vault"]

        base_amt, base_dec = await get_balance(client, base_vault)
        quote_amt, quote_dec = await get_balance(client, quote_vault)
        base = base_amt / (10 ** base_dec)
        quote = quote_amt / (10 ** quote_dec)

        price = quote / base if base > 0 else 0
        supply, sup_dec = await get_token_supply(client, TOKEN_MINT)
        supply_norm = supply / (10 ** sup_dec)
        mcap = price * supply_norm

        return {
            "status": "success",
            "token_mint": TOKEN_MINT,
            "base_vault": base_vault,
            "quote_vault": quote_vault,
            "base_balance": base,
            "quote_balance": quote,
            "price_wsol": price,
            "supply": supply_norm,
            "market_cap_wsol": mcap
        }


@app.route("/")
def index():
    """Trigger the fetch and return JSON."""
    result = asyncio.run(run_one_fetch())
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)