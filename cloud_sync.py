import os
import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666"

CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]

def get_driver():
    for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(env_var, None)

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
    options.add_argument(f'--proxy-server=http://{proxy_addr}')
    options.add_argument("--proxy-bypass-list=localhost;127.0.0.1;*.local")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print("🚀 开始抓取流程...")
    driver = get_driver()

    # 1. 验证 IP 归属地
    try:
        driver.get("https://ifconfig.me/ip")
        ip = driver.execute_script("return document.body.innerText").strip()
        print(f"🕵️ 浏览器当前出口 IP: {ip}")
    except: pass

    for cid in CHANNELS:
        try:
            print(f"📡 处理频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(35) # 给广告和检测预留时间

            # 2. 检查是否被 Geo-block
            page_text = driver.page_source
            if "仅限台湾" in page_text or "收看限制" in page_text:
                print(f"❌ {cid} 失败: IP 归属地非台湾，被网站屏蔽")
                continue

            asset_id = None
            # 3. 搜索流地址
            for req in reversed(driver.requests):
                u = req.url
                if 'playlist' in u and 'index.m3u8' in u:
                    try:
                        # 格式通常是 .../playlist/ASSET_ID/index.m3u8
                        asset_id = u.split('/')[-2]
                        break
                    except: continue

            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} -> {asset_id} (Worker: {res.status_code})")
            else:
                print(f"❌ {cid} 失败: 未捕获到 m3u8。请确认页面是否已成功加载视频。")

            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 异常: {e}")

    driver.quit()
    print("🏁 任务完成")

if __name__ == "__main__":
    sync()
