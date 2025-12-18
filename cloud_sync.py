import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller

# 1. 环境准备
chromedriver_autoinstaller.install()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

def sync_channel(channel_id):
    driver = webdriver.Chrome(options=options)
    try:
        print(f"正在抓取: {channel_id}...")
        driver.get(f"https://www.ofiii.com/channel/watch/{channel_id}")
        
        asset_id = None
        # 等待并拦截 master.m3u8 链接
        for i in range(20): # 最多等20秒
            for request in driver.requests:
                if 'master.m3u8' in request.url:
                    asset_id = request.url.split('/')[-2]
                    break
            if asset_id: break
            time.sleep(1)

        if asset_id:
            # 推送到你的 Cloudflare Worker
            # 这里的 URL 换成你 Worker 的真实地址
            resp = requests.post("https://你的Worker域名/update_key", json={
                "id": channel_id,
                "key": asset_id,
                "pw": "your_password_666" # 需与 Worker 里的密码一致
            })
            print(f"✅ {channel_id} 同步成功: {resp.text}")
        else:
            print(f"❌ {channel_id} 抓取失败")
    finally:
        driver.quit()

# 龙华频道列表
channels = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]

if __name__ == "__main__":
    for cid in channels:
        sync_channel(cid)
