# main.py
# Auto Vault Fetch + Token Data Tracker (Solana Pump.fun)
# Flask server for dynamic token vault info
# Compatible with solana==0.30.2, solders==0.18.1

import asyncio
from flask import Flask, jsonify, request
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.types import MemcmpOpts

# ===== CONFIG =====
RPC_URL = "https://solana-mainnet.rpc.extrnode.com/0fce7e9a-3879-45d2-b543-a7988fd05869"
PUMPFUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P6"  # Pump.fun AMM program
DEFAULT_TOKEN_MINT = "64BX1uPFBZnNmEZ9USV1NA2q2SoeJEKZF2hu7cB6pump"  # default token
WSOL_DECIMALS = 9
TOKEN_DECIMALS = 6
# ==================

app = Flask(__name__)

async def fetch_vaults(token_mint: str):
    client = AsyncClient(RPC_URL)
    try:
        mint_pubkey = Pubkey.from_string(token_mint)
        program_pubkey = Pubkey.from_string(PUMPFUN_PROGRAM_ID)

        resp = await client.get_program_accounts(
            program_pubkey,
            encoding="jsonParsed",
            filters=[MemcmpOpts(offset=0, bytes=str(mint_pubkey))]
        )

        value = getattr(resp, "value", None)
        if not value:
            await client.close()
            return {"error": f"No vaults found for mint {token_mint}"}

        pool = value[0]
        data = pool.account.data
        base_vault = data["parsed"]["info"]["baseVault"]
        quote_vault = data["parsed"]["info"]["quoteVault"]

        # Fetch balances
        base_amt, base_dec = await get_balance(client, base_vault)
        quote_amt, quote_dec = await get_balance(client, quote_vault)

        # Normalize balances
        base = base_amt / (10 ** base_dec)
        quote = quote_amt / (10 ** quote_dec)

        # Token supply
        supply, sup_dec = await get_token_supply(client, token_mint)
        supply_norm = supply / (10 ** sup_dec)
        price = quote / base if base > 0 else 0
        mcap = price * supply_norm

        await client.close()
        return {
            "token_mint": token_mint,
            "base_vault": base_vault,
            "quote_vault": quote_vault,
            "base": base,
            "quote": quote,
            "price_in_wsol": price,
            "supply": supply_norm,
            "market_cap": mcap
        }

    except Exception as e:
        await client.close()
        return {"error": str(e)}


async def get_balance(client: AsyncClient, account: str):
    try:
        resp = await client.get_token_account_balance(Pubkey.from_string(account))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


async def get_token_supply(client: AsyncClient, mint: str):
    try:
        resp = await client.get_token_supply(Pubkey.from_string(mint))
        val = getattr(resp, "value", None)
        if not val:
            return 0, 0
        return int(val.amount), int(val.decimals)
    except Exception:
        return 0, 0


@app.route("/")
def home():
    return f"🚀 Pump.fun Vault API running! Use /vault to fetch default token info or /vault/<token_mint> to fetch specific token."


@app.route("/vault")
def vault_default():
    """Fetch vault info for default token mint"""
    return jsonify(asyncio.run(fetch_vaults(DEFAULT_TOKEN_MINT)))


@app.route("/vault/<token_mint>")
def vault(token_mint):
    """Fetch vault info for a given token mint"""
    return jsonify(asyncio.run(fetch_vaults(token_mint)))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)