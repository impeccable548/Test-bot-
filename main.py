import asyncio
import websockets
import json

# PumpFun WebSocket URL
WS_URL = "wss://pumpportal.fun/api/data"

async def get_trending():
    async with websockets.connect(WS_URL) as ws:
        # Subscribe to trending tokens
        await ws.send(json.dumps({
            "method": "trending",
            "params": {}
        }))

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)

                if "result" in data and "tokens" in data["result"]:
                    tokens = data["result"]["tokens"]

                    print("\n🔥 Top 10 PumpFun Trending Tokens 🔥")
                    for i, token in enumerate(tokens[:10], start=1):
                        print(f"{i}. {token['name']} ({token['symbol']}) | "
                              f"CA: {token['mint']} | "
                              f"MCAP: {token.get('marketCapUsd', 'N/A')}")

            except Exception as e:
                print("Error:", e)
                break

if __name__ == "__main__":
    asyncio.run(get_trending())