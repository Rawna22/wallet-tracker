import os
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# --- Konstanta Chain IDs (Covalent) ---
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

# --- ENV ---
COVALENT_API_KEY   = os.getenv("COVALENT_API_KEY", "")
WALLET_ADDRESS     = os.getenv("WALLET_ADDRESS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Pilih chain via ENV, default = semua di mapping
ENABLED_CHAINS = [
    c.strip() for c in os.getenv(
        "COVALENT_CHAINS",
        ",".join(COVALENT_CHAIN_IDS.keys())
    ).split(",")
    if c.strip() in COVALENT_CHAIN_IDS
]

def _dec(x):
    """Safe Decimal conversion."""
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(0)

def fetch_top_tokens_covalent(chain_name: str, wallet: str, api_key: str, top_n: int = 10):
    """Ambil top N token (berdasarkan USD) untuk 1 wallet di 1 chain via Covalent."""
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
        if it.get("type") == "nft":
            continue
        decimals = int(it.get("contract_decimals") or 18)
        raw = _dec(it.get("balance"))
        amt = raw / (Decimal(10) ** decimals) if decimals else raw
        px  = _dec(it.get("quote_rate"))
        usd = (amt * px) if px else Decimal(0)
        if amt > 0:
            rows.append({
                "symbol": (it.get("contract_ticker_symbol") or "?").upper(),
                "amount": amt,
                "usd": usd,
            })

    rows.sort(key=lambda x: x["usd"], reverse=True)
    return rows[:top_n]

def build_tokens_message_multi_chain(wallet: str, api_key: str, chains: list[str], top_n: int = 10) -> str:
    """Buat teks Telegram yang berisi token per chain untuk satu wallet."""
    sections = []
    for chain in chains:
        tokens = fetch_top_tokens_covalent(chain, wallet, api_key, top_n=top_n)
        if not tokens:
            continue
        lines = [f"*{chain}*"]
        for t in tokens:
            amount_str = f"{t['amount']:.6f}".rstrip('0').rstrip('.')
            usd_str = f" (${t['usd']:.2f})" if t["usd"] > 0 else ""
            lines.append(f"• *{t['symbol']}*: {amount_str}{usd_str}")
        sections.append("\n".join(lines))

    if not sections:
        return "Tidak ada token yang terdeteksi dari chain yang dipilih."
    return f"💼 *Wallet Tokens per Chain*\n\n" + "\n\n".join(sections)

def send_telegram_markdown(text: str):
    """Kirim pesan Markdown ke Telegram, auto-split bila >4096 char."""
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    maxlen = 4096
    msg = text
    while msg:
        chunk = msg[:maxlen]
        # potong di newline kalau memungkinkan agar rapi
        if len(msg) > maxlen:
            cut = chunk.rfind("\n")  # <-- pakai kutip biasa
            if cut > 2000:
                chunk = msg[:cut]
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        })
        msg = msg[len(chunk):]

if __name__ == "__main__":
    token_msg = build_tokens_message_multi_chain(
        WALLET_ADDRESS,
        COVALENT_API_KEY,
        ENABLED_CHAINS,
        top_n=10
    )

    final_msg = token_msg
    print(final_msg)
    send_telegram_markdown(final_msg)