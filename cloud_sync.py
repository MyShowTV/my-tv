import os
import requests
import time
import json
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# --- 请修改以下信息 ---
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "这里填你Workers里设置的密码" 
# --------------------

CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]

def get_driver():
    chromedriver_autoinstaller.install()
    proxy = "127.0.0.1:7890"
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--proxy-server=http://{proxy}')
    
    sw_options = {
        'proxy': {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    driver = get_driver()
    print("🚀 启动抓取流程...")
    
    for cid in CHANNELS:
        try:
            print(f"📡 正在处理频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            time.sleep(30)  # 给代理一点缓冲时间

            asset_id = None
            # 搜索包含 m3u8 的请求
            for req in reversed(driver.requests):
                if 'playlist' in req.url and 'index.m3u8' in req.url:
                    # 提取 URL 中的 ID 部分
                    asset_id = req.url.split('/')[-2]
                    break
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 同步成功, Key: {asset_id}")
            else:
                print(f"❌ {cid} 未找到播放地址")
                
            del driver.requests # 清除请求历史，准备下一个频道
        except Exception as e:
            print(f"💥 {cid} 出错: {str(e)}")

    driver.quit()

if __name__ == "__main__":
    sync()
