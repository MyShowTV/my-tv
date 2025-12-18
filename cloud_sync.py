import os
import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666"

CHANNELS = [
    "litv-longturn03",
    "litv-longturn21",
    "litv-longturn18",
    "litv-longturn11",
    "litv-longturn12",
    "litv-longturn01",
    "litv-longturn02"
]

def get_driver():
    for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(env_var, None)

    print("📥 初始化 Chrome 驱动中...")
    chromedriver_autoinstaller.install()

    proxy_addr = "127.0.0.1:7890"

    sw_options = {
        'proxy': {
            'http': f'http://{proxy_addr}',
            'https': f'http://{proxy_addr}',
            'no_proxy': 'localhost,127.0.0.1'
        },
        'verify_ssl': False
    }

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)


def sync():
    print("🚀 开始抓取流程...")
    driver = get_driver()

    try:
        driver.get("https://ifconfig.me/ip")
        print(f"🕵️ 代理出口 IP: {driver.page_source.strip()}")
    except Exception as e:
        print(f"⚠️ IP 验证失败: {e}")

    for cid in CHANNELS:
        try:
            print(f"📡 处理频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(30)

            asset_id = None
            for req in driver.requests:
                u = req.url
                if 'playlist' in u and ('litv' in u or cid in u):
                    try:
                        parts = u.split('/')
                        asset_id = parts[parts.index('playlist') + 1]
                        break
                    except:
                        continue

            if asset_id:
                res = requests.post(WORKER_URL, json={
                    "id": cid, "key": asset_id, "pw": AUTH_PW
                }, timeout=10)
                print(f"✅ {cid} -> {asset_id} (Worker: {res.status_code})")
            else:
                print(f"❌ {cid} 无法嗅探到 m3u8 请求")

            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 异常: {e}")

    driver.quit()
    print("🏁 所有任务完成")


if __name__ == "__main__":
    sync()
