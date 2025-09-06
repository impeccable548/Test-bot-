import requests

# Endpoint to fetch trending tokens
url = "https://pumpportal.fun/api/trade-local"

# Request top tokens
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    top_10 = data[:10]  # assuming API returns a list of tokens
    print("Top 10 trending tokens:")
    for i, token in enumerate(top_10, start=1):
        print(f"{i}. {token['name']} ({token['mint']})")  # adjust keys based on actual API response
else:
    print(f"Failed to fetch tokens. Status code: {response.status_code}")
                    