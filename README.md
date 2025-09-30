# 🛠️ Wallet Tracker  

Script Python sederhana untuk cek saldo wallet & token Web3.  
Bisa dijalankan manual atau otomatis lewat **GitHub Actions**, serta mendukung notifikasi via **Telegram Bot**.  

---

## ✨ Fitur  

- 🔍 Cek saldo native ETH di beberapa chain (Ethereum, Base, zkSync)  
- 💰 Ambil saldo token ERC-20 via **Covalent API**  
- 📜 Lihat riwayat transaksi wallet  
- 🤖 Kirim ringkasan otomatis ke **Telegram** (opsional)  
- ⚡ Bisa dijalankan manual atau otomatis lewat **GitHub Actions**  

---

## ⚡ Instalasi Cepat  

```bash
git clone https://github.com/Rawna22/wallet-tracker.git
cd wallet-tracker
pip install -r requirements.txt

---

## 🔑 Konfigurasi .env
Buat file .env di root folder repo (⚠️ jangan dipush ke GitHub).

⚡ RPC endpoints

ETHEREUM_RPC=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
BASE_RPC=https://mainnet.base.org
ZKSYNC_RPC=https://zksync2-mainnet.zksync.io

COVALENT_API_KEY=ckey_xxxxxxxxxxxxxxxxxxxxx

WALLET_ADDRESS=

---

## ▶️ Cara Menjalankan

python wallet_tracker.py
