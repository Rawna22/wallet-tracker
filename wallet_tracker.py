import os
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# --- Konstanta Chain Covalent ---
COVALENT_CHAIN_IDS = {
    "Ethereum": 1,
    "Base": 8453,
    "Optimism": 10,
    "zkSync": 324,
    # bisa tambah chain lain
}

# --- Config dari ENV ---
COVALENT_API_KEY   = os.getenv("COVALENT_API_KEY", "")
WALLET_ADDRESS     = os.getenv("WALLET_ADDRESS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

def _dec(x):
    try:
        return Decimal(str(x))
    except:
        return Decimal(0)

def fetch_top_tokens_covalent(chain_name: str, wallet: str, api_key: str, top_n: int = 5):
    cid = COVALENT_CHAIN_IDS.get(chain_name)
    if not (cid and api_key and wallet):
        return []
    url = f"https://api.covalenthq.com/v1/{cid}/address/{wallet}/balances_v2/"
    try:
        r = requests.get(url, params={"key": api_key, "nft": False}, timeout=20)
    except Exception:
        return []
    if r.status_code != 200:
        return []
    items = (r.json() or {}).get("data", {}).get("items", []) or []
    out = []
    for it in items:
        if it.get("type") == "nft":
            continue
        decs = it.get("contract_decimals") or 0
        raw = _dec(it.get("balance"))
        amt = raw / (Decimal(10) ** decs) if decs else raw
        price = _dec(it.get("quote_rate"))
        usd = amt * price if price else None
        out.append({
            "symbol": it.get("contract_ticker_symbol") or "",
            "amount": amt,
            "usd": usd,
        })
    out.sort(key=lambda x: (x["usd"] or Decimal(0)), reverse=True)
    return out[:top_n]

def build_tokens_message_multi_chain(wallet: str, api_key: str, chains: list[str], top_n: int = 5):
    sections = []
    for ch in chains:
        toks = fetch_top_tokens_covalent(ch, wallet, api_key, top_n)
        if not toks:
            continue
        lines = [f"*{ch}