# 🛠️ Wallet Tracker (Mini Guide)

Script Python sederhana untuk cek saldo wallet & token Web3.

---

## ⚡ Instalasi Cepat
```bash
git clone https://github.com/Rawna22/wallet-tracker.git
cd wallet-tracker
pip install -r requirements.txt

Config .env
Buat file .env di root (jangan di-push ke GitHub):

ETHEREUM_RPC=https://mainnet.infura.io/v3/YOUR_KEY
BASE_RPC=https://mainnet.base.org
ZKSYNC_RPC=https://zksync2-mainnet.zksync.io
COVALENT_API_KEY=YOUR_COVALENT_KEY
WALLET_ADDRESS=

Opsional (untuk notifikasi Telegram):

TELEGRAM_BOT_TOKEN=xxxx
TELEGRAM_CHAT_ID=xxxx

Jalankan

python wallet_tracker.py
[Ethereum] Native balance: 0.5234 ETH
[Base] Native balance: 2.10 ETH

Otomatis (GitHub Actions)

Tambahkan workflow .github/workflows/tracker.yml dan simpan API key di Secrets repo.
