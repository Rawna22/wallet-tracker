import os
import requests
from decimal import Decimal
from web3 import Web3
from dotenv import load_dotenv

# --- Konstanta Chain IDs Covalent ---
COVALENT_CHAIN_IDS = {
    "Ethereum": 1,
    "Base": 8453,
    "Optimism": 10,
    "zkSync": 324,
    "Polygon": 137,
    "Arbitrum": 42161,
    "BSC": 56,
    "Avalanche": 43114,
    "Fantom": 250,
}

def _dec(x):
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(0)

def fetch_top_tokens_covalent(chain_name: str, wallet: str, api_key: str, top_n: int = 10):
    """
    Ambil top N token (berdasarkan USD value) untuk 1 wallet di 1 chain via Covalent.
    Return: list[{"symbol","name","amount","usd"}]
    """
    cid = COVALENT_CHAIN_IDS.get(chain_name)
    if not (cid and api_key and wallet):
        return []

    url = f"https://api.covalenthq.com/v1/{cid}/address/{wallet}/balances_v2/"
    try:
        r = requests.get(url, params={"key": api_key, "nft": False}, timeout=25)
    except Exception:
        return []
    if r.status_code != 200:
        return []

    items = (r.json() or {}).get("data", {}).get("items", []) or []
    rows = []
    for it in items:
        # skip NFT
        if it.get("type") == "nft":
            continue
        decimals = int(it.get("contract_decimals") or 18)
        raw = _dec(it.get("balance"))
        amt = raw / (Decimal(10) ** decimals) if decimals else raw
        px  = _dec(it.get("quote_rate"))
        usd = (amt * px) if px else None

        rows.append({
            "symbol": (it.get("contract_ticker_symbol") or "?").upper(),
            "name": it.get("contract_name") or "",
            "amount": amt,
            "usd": usd if usd is not None else Decimal(0),
        })

    # urutkan berdasarkan USD tertinggi
    rows.sort(key=lambda x: x["usd"], reverse=True)
    return rows[:top_n]

# --- Params dari ENV ---
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY", "")
WALLET_ADDRESS   = os.getenv("WALLET_ADDRESS", "")
# Pilih chain mana yang mau dimasukkan (default Ethereum,Base,Optimism,zkSync)
ENABLED_CHAINS = [
    c.strip() for c in (os.getenv("COVALENT_CHAINS", "Ethereum,Base,Optimism,zkSync").split(","))
    if c.strip() in COVALENT_CHAIN_IDS
]

# ... (setelah kamu sudah bikin 'message' native balance)
tokens_msg = ""
if COVALENT_API_KEY and WALLET_ADDRESS:
    tokens_msg = build_tokens_message_multi_chain(
        WALLET_ADDRESS,
        COVALENT_API_KEY,
        ENABLED_CHAINS,
        top_n=10,  # bisa diatur
    )

final_msg = message  # message kamu yang lama (native balance / ringkasan lain)
if tokens_msg:
    final_msg += "\n\n" + tokens_msg

# --- kirim Telegram (pastikan pakai parse_mode Markdown) ---
def send_telegram_markdown(text: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # split bila > 4096
    chunks = []
    while len(text) > 4096:
        cut = text.rfind("\n", 0, 4000)
        if cut <= 0: cut = 4000
        chunks.append(text[:cut])
        text = text[cut:]
    chunks.append(text)
    for part in chunks:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"})

send_telegram_markdown(final_msg)
print(final_msg)

# --- Config dari environment ---
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY", "")
WALLET_ADDRESS   = os.getenv("WALLET_ADDRESS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Load .env (paksa override biar selalu update)
load_dotenv(override=True)

# Config from .env
ETHEREUM_RPC = os.getenv("ETHEREUM_RPC")
BASE_RPC = os.getenv("BASE_RPC")
ZKSYNC_RPC = os.getenv("ZKSYNC_RPC")

COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

WALLET = os.getenv("WALLET_ADDRESS", "0x2e5392f3d727a5c0e5a2e4a3530c2254dbce205d")
# Normalisasi address agar sesuai checksum
WALLET = Web3.to_checksum_address(WALLET)

# Setup Web3 clients (hanya kalau RPC tersedia)
w3_eth = Web3(Web3.HTTPProvider(ETHEREUM_RPC)) if ETHEREUM_RPC else None
w3_base = Web3(Web3.HTTPProvider(BASE_RPC)) if BASE_RPC else None
w3_zksync = Web3(Web3.HTTPProvider(ZKSYNC_RPC)) if ZKSYNC_RPC else None


def from_wei(value_wei, decimals=18):
    """Konversi dari Wei ke Decimal ETH"""
    return Decimal(value_wei) / (Decimal(10) ** decimals)
def from_wei(value_wei, decimals=18):
    return Decimal(value_wei) / (Decimal(10) ** decimals)

def print_native_balance(w3_client, chain_name):
    if not w3_client:
        print(f"[{chain_name}] RPC not configured.")
        return None
    try:
        bal = w3_client.eth.get_balance(WALLET)
        eth_amount = from_wei(bal, 18)
        print(f"[{chain_name}] Native balance: {eth_amount} (wei: {bal})")
        return eth_amount
    except Exception as e:
        print(f"[{chain_name}] Error getting balance: {e}")
        return None

# Covalent helper: get token balances for given chain_id
# Covalent chain ids: Ethereum mainnet = 1, Base = 8453, zkSync = 324 (example) — check Covalent docs for exact IDs
COVALENT_CHAIN_IDS = {
    "ethereum": 1,
    "base": 8453,
    "zksync": 324,
}

def covalent_get_token_balances(chain_key):
    """
    Uses Covalent /v1/{chain_id}/address/{address}/balances_v2/
    returns list of token balances (including native)
    """
    if not COVALENT_API_KEY:
        print("COVALENT_API_KEY not set. Skipping token balances (Covalent).")
        return []
    chain_id = COVALENT_CHAIN_IDS.get(chain_key)
    if not chain_id:
        print(f"No chain id mapped for {chain_key}")
        return []
    url = f"https://api.covalenthq.com/v1/{chain_id}/address/{WALLET}/balances_v2/"
    params = {"key": COVALENT_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("items", [])
        results = []
        for it in items:
            balance = int(it.get("balance", 0))
            contract_ticker = it.get("contract_ticker_symbol") or it.get("logo_url") or "NATIVE"
            decimals = it.get("contract_decimals") or 0
            human = from_wei(balance, decimals) if decimals>0 else Decimal(balance)
            results.append({
                "symbol": contract_ticker,
                "contract_address": it.get("contract_address"),
                "balance_raw": balance,
                "decimals": decimals,
                "human": str(human)
            })
        return results
    except Exception as e:
        print("Covalent API error:", e)
        return []

def get_eth_tx_history_covalent(chain_key, page_size=50):
    if not COVALENT_API_KEY:
        print("COVALENT_API_KEY not set. Skipping tx history (Covalent).")
        return []
    chain_id = COVALENT_CHAIN_IDS.get(chain_key)
    if not chain_id: return []
    url = f"https://api.covalenthq.com/v1/{chain_id}/address/{WALLET}/transactions_v2/"
    params = {"key": COVALENT_API_KEY, "page-size": page_size}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("items", [])
        return items
    except Exception as e:
        print("Covalent transactions error:", e)
        return []

def send_telegram(msg: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram not configured or missing values. Skipping telegram.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram send error:", e)

def main():
    print("=== Wallet Tracker Summary ===")
    print("Wallet:", WALLET)
    # Native balances
    print_native_balance(w3_eth, "Ethereum")
    print_native_balance(w3_base, "Base")
    print_native_balance(w3_zksync, "zkSync")

    print("\n--- Covalent token balances (Ethereum) ---")
    eth_tokens = covalent_get_token_balances("ethereum")
    for tok in eth_tokens[:30]:
        print(f"{tok['symbol']:10} {tok['human']:>20}  contract: {tok['contract_address']}")
    # Optional: send a short summary via telegram
    if eth_tokens:
        top = eth_tokens[:5]
        msg = "Wallet balances summary (top tokens):\n" + "\n".join([f"{t['symbol']}: {t['human']}" for t in top])
        send_telegram(msg)

    # Transactions example
    print("\n--- Recent transactions (Ethereum via Covalent) ---")
    txs = get_eth_tx_history_covalent("ethereum", page_size=20)
    for tx in txs[:10]:
        print(f"Tx hash: {tx.get('tx_hash')}  value_native: {tx.get('value')}")
    print("\nDone.")

if __name__ == "__main__":
    main()
# misalnya sudah bikin text dari hasil loop multi-chain
text = "💼 Wallet summary ..."

# gunakan text, bukan message
final_msg = text
send_to_telegram(final_msg)