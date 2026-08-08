import os, time, requests

TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT = os.environ.get("TG_CHAT_ID")
SEEN = set()

PROXY_URL = os.environ.get("GMGN_PROXY_URL", "https://gmgn-proxy.workers.dev")

def poll_gmgn():
    print("Fetching GMGN via CF Worker Proxy...")
    res = requests.get(f"{PROXY_URL}/api/v1/rank/sol/swaps/5m")
    if res.status_code != 200:
        return print(f"Error {res.status_code}")
    
    data = res.json()
    rank = data.get("data", {}).get("rank", [])
    print(f"Got {len(rank)} tokens from GMGN.")
    
    for t in rank:
        addr = t.get("address")
        if not addr or addr in SEEN: continue
        
        mc = float(t.get("market_cap", 0) or 0)
        vol_5m = float(t.get("volume", 0) or 0) # volume 5m dari parameter query asli GMGN
        tx_5m = int(t.get("swaps", 0) or 0) 
        
        # Tambahkan filter holder (opsional, karena GMGN API punya data ini)
        hc = int(t.get("holder_count", 0) or 0)
        
        # Filter total fees minimal 30 SOL (diambil dari gas_fee pada endpoint GMGN)
        gas_fee = float(t.get("gas_fee", 0) or 0)
        
        # ponytail: prevent memory leak, batasi SEEN history
        if len(SEEN) > 10000:
            SEEN.clear()
        
        print(f"Check: {t.get('symbol')} | MC: {mc} | Vol: {vol_5m} | TX: {tx_5m} | Fee(SOL): {gas_fee:.1f}")
        
        if mc >= 250000 and vol_5m >= 10000 and tx_5m >= 100 and gas_fee >= 30:
            SEEN.add(addr)
            symbol = t.get('symbol')
            msg = f"🚨 <b>{symbol}</b> (GMGN)\nMC: ${mc:,.0f} | Vol(5m): ${vol_5m:,.0f} | TX: {tx_5m} | Fees: {gas_fee:.1f} SOL\nCA: <code>{addr}</code>\n<a href='https://gmgn.ai/sol/token/{addr}'>Trade on GMGN</a>"
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                          json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True})
            print(f"Alerted: {symbol}")

if __name__ == "__main__":
    assert TG_TOKEN and TG_CHAT, "Set ENV: TG_BOT_TOKEN & TG_CHAT_ID"
    print("Mulai polling GMGN (15s)...")
    while True:
        try: poll_gmgn()
        except Exception as e: print(f"Error: {e}")
        time.sleep(15)
