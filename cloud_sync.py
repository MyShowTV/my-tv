import time
import requests
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# ================= 配置区 =================
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "你的密码"  # 填入 Workers 的认证密码
PROXY = "127.0.0.1:7890"

CHANNELS = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]
# ==========================================

def get_driver():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--proxy-server=http://{PROXY}')
    
    sw_options = {
        'proxy': {
            'http': f'http://{PROXY}',
            'https': f'http://{PROXY}',
        },
        'verify_ssl': False 
    }
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def main():
    driver = get_driver()
    print("🚀 启动抓取流程...")
    
    for cid in CHANNELS:
        try:
            print(f"📡 抓取频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(45) 

            asset_id = None
            for req in reversed(driver.requests):
                if req.response and 'index.m3u8' in req.url:
                    asset_id = req.url.split('/')[-2]
                    break
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ 成功: {cid} -> {asset_id} (Code: {res.status_code})")
            else:
                print(f"❌ 失败: {cid} 未捕获到 m3u8")
                
            del driver.requests
        except Exception as e:
            print(f"💥 错误 {cid}: {e}")

    driver.quit()

if __name__ == "__main__":
    main()
