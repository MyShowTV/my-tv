import requests
import time
import os
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# 请确保密码与 Worker 里的 "your_password_666" 一致
WORKER_URL = "https://你的worker域名.workers.dev/update_key"
AUTH_PW = "your_password_666"

# 完整的 7 个龙华 ID
CHANNELS = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]

def sync():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)
    
    for cid in CHANNELS:
        print(f"正在抓取: {cid}")
        try:
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(10) # 给页面充足加载时间
            
            asset_id = None
            for req in driver.requests:
                if 'master.m3u8' in req.url:
                    asset_id = req.url.split('/')[-2]
                    break
            
            if asset_id:
                requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW})
                print(f"✅ {cid} 同步成功: {asset_id}")
            else:
                print(f"❌ {cid} 未找到地址")
            del driver.requests 
        except Exception as e:
            print(f"错误: {e}")
            
    driver.quit()

if __name__ == "__main__":
    sync()
