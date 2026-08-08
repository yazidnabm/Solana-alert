# Solana GMGN Alert Bot

Bot Telegram ringan untuk mendeteksi *trending token* di jaringan Solana berdasarkan data [GMGN.ai](https://gmgn.ai). 
Bot ini berjalan di *background* menggunakan `screen` dan menembak GMGN API lewat Cloudflare Worker Proxy untuk menghindari blokir WAF (Cloudflare 403 Forbidden) di IP Datacenter/VPS.

## Kriteria Filter
Notifikasi Telegram hanya akan dikirim setiap 15 detik jika ada koin yang memenuhi kriteria *spike* berikut di waktu bersamaan:
- **Market Cap**: $\ge$ $250,000
- **Volume (5 menit)**: $\ge$ $10,000
- **Transaksi (5 menit)**: $\ge$ 100 kali
- **Total Fees**: $\ge$ 30 SOL

## Setup & Instalasi (Ubuntu/Linux)

1. **Clone Repo**
   ```bash
   git clone https://github.com/yazidnabm/Solana-alert.git
   cd Solana-alert
   ```

2. **Buat Virtual Environment & Install Dependensi**
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install requests
   ```

3. **Konfigurasi Environment**
   Buat file `.env` di folder root dan isi dengan variabel berikut:
   ```env
   TG_BOT_TOKEN="token_telegram_bot_kamu"
   TG_CHAT_ID="id_chat_atau_grup_tujuan"
   GMGN_PROXY_URL="https://url-cloudflare-worker-kamu.workers.dev"
   ```

4. **Jalankan Bot di Background (Screen)**
   Beri akses eksekusi ke `start.sh` dan jalankan lewat screen.
   ```bash
   chmod +x start.sh
   screen -dmS gmgn-alert bash -c './start.sh'
   ```

## Cloudflare Proxy Bypass
Karena WAF GMGN menolak *traffic* dari Datacenter (AWS/DO/Hetzner), bot ini me-rutekan request lewat *Edge Worker* Cloudflare.

Jika kamu belum punya Worker, buat `worker.js` di dashboard Cloudflare kamu dengan kode berikut:
```javascript
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const targetUrl = new URL(url.pathname + url.search, "https://gmgn.ai");
    
    const newRequest = new Request(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
    
    newRequest.headers.set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36");
    newRequest.headers.set("Accept", "application/json");
    newRequest.headers.set("Referer", "https://gmgn.ai/");
    newRequest.headers.delete("cf-worker");
    newRequest.headers.delete("cf-connecting-ip");
    
    return fetch(newRequest);
  }
};
```