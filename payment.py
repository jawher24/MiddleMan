import aiohttp
from config import TRON_WALLET, TRONGRID_API_KEY, USDT_CONTRACT

async def check_payment(deals):
    url = f"https://api.trongrid.io/v1/accounts/{TRON_WALLET}/transactions/trc20?limit=50"
    headers = {'TRON-PRO-API-KEY': TRONGRID_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            txs = data.get("data", [])
            for tx in txs:
                if tx["to"] == TRON_WALLET and tx["token_info"]["symbol"] == "USDT":
                    sender = tx["from"]
                    amount = float(tx["value"]) / 1_000_000
                    txid = tx["transaction_id"]
                    for deal in deals:
                        if float(deal[3]) == amount and deal[7] != txid:
                            return deal[0], txid
    return None, None