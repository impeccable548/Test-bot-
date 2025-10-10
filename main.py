async def main():
    client = AsyncClient(RPC_URL)
    try:
        vaults = await auto_vaults(client, TOKEN_MINT)

        if not vaults:
            print("⚠️ No vaults found. Maybe token graduated from Pump.fun.")
        else:
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
    except Exception as e:
        print(f"🔥 Unexpected error: {e}")
    finally:
        await client.close()
        print("✅ Client connection closed.")

    # 🕐 Keep alive briefly to avoid Render shutdown
    await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())