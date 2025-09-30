"""
wallet_tracker.py
Script sederhana untuk:
- cek saldo native (ETH / Base / zkSync via RPC)
- cek token balances & token transfers via Covalent API (lebih lengkap)
- kirim notifikasi via Telegram (opsional)

Konfigurasi via .env
"""

import os
import time
import requests
from decimal import Decimal
from web3 import Web3
from dotenv import load_dotenv

from dotenv import load_dotenv
load_dotenv(override=True)

# Config from .env
ETHEREUM_RPC = os.getenv("ETHEREUM_RPC")
BASE_RPC = os.getenv("BASE_RPC")
ZKSYNC_RPC = os.getenv("ZKSYNC_RPC")

COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

WALLET = os.getenv("WALLET_ADDRESS", "0x2e5392f3d727a5c0e5a2e4a3530c2254dbce205d")
# normalize
WALLET = Web3.to_checksum_address(WALLET)

# Setup Web3 clients (only if RPC provided)
w3_eth = Web3(Web3.HTTPProvider(ETHEREUM_RPC)) if ETHEREUM_RPC else None
w3_base = Web3(Web3.HTTPProvider(BASE_RPC)) if BASE_RPC else None
w3_zksync = Web3(Web3.HTTPProvider(ZKSYNC_RPC)) if ZKSYNC_RPC else None

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
