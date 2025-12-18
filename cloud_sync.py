import os
import requests
import time
import json
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666"
CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]

def get_driver():
    for env in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(env, None)

    chromedriver_autoinstaller.install()
    proxy = "127.0.0.1:7890"

    sw_options = {
        'proxy': {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}',
            'no_proxy': 'localhost,127.0.0.1'
        },
        'verify_ssl': False
    }

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument(f'--proxy-server=http://{proxy}')
    options.add_argument("--proxy-bypass-list=localhost;127.0.0.1;*.local")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    driver = get_driver()
    
    # 地区二次校验
    try:
        driver.get("http://ip-api.com/json/")
        data = json.loads(driver.find_element("tag name", "pre").text)
        print(f"🕵️ 浏览器实际出口: {data.get('query')} ({data.get('countryCode')})")
        if data.get('countryCode') != 'TW':
            print("🛑 非台湾 IP，根据版权保护机制停止抓取。")
            driver.quit()
            return
    except Exception as e:
        print(f"⚠️ 校验失败: {e}")

    for cid in CHANNELS:
        try:
            print(f"📡 抓取频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(40) # 延长等待确保流加载

            asset_id = None
            for req in reversed(driver.requests):
                if 'playlist' in req.url and 'index.m3u8' in req.url:
                    try:
                        asset_id = req.url.split('/')[-2]
                        if len(asset_id) > 20: break
                    except: continue

            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} -> {asset_id} (Worker: {res.status_code})")
            else:
                print(f"❌ {cid} 未捕获到地址。")
            
            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 错误: {e}")

    driver.quit()
    print("🏁 任务完成")

if __name__ == "__main__":
    sync()
