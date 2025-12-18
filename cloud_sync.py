import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller

# 配置区
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666"

chromedriver_autoinstaller.install()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

def sync_cid(cid):
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
        asset_id = None
        for _ in range(20): # 等待页面加载
            for req in driver.requests:
                if 'master.m3u8' in req.url:
                    asset_id = req.url.split('/')[-2]
                    break
            if asset_id: break
            time.sleep(1)
        
        if asset_id:
            requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW})
            print(f"✅ {cid} 同步成功")
    finally:
        driver.quit()

if __name__ == "__main__":
    channels = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]
    for c in channels:
        sync_cid(c)
