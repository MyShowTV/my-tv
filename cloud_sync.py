import requests
import time
import os
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# ====== 配置区 ======
# 请替换为你自己的 Worker 地址
WORKER_URL = "https://你的域名.workers.dev/update_key"
AUTH_PW = "your_password_666"

CHANNELS = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]

def get_driver():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    # 模拟移动端，通常移动端的流地址更容易解析且没有复杂的广告
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
    
    driver = webdriver.Chrome(options=options)
    return driver

def sync_all():
    print(f"⏰ 任务启动: {time.strftime('%H:%M:%S')}")
    driver = get_driver()
    
    for cid in CHANNELS:
        print(f"🔍 正在检索频道: {cid}")
        try:
            # 访问官方频道页
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 1. 模拟点击以激活播放
            time.sleep(12) 
            try:
                driver.execute_script("document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).click();")
                print("🖱️ 已模拟触发播放...")
            except:
                pass
            
            asset_id = None
            # 2. 核心提取逻辑：根据你发现的特征进行匹配
            # 在 30 秒内扫描所有流量
            for _ in range(30):
                for req in driver.requests:
                    # 匹配规则：URL 包含频道代号 且 包含 .m3u8
                    if cid in req.url and '.m3u8' in req.url:
                        # 典型的 URL 结构: .../playlist/ASSET_ID/litv-longturnXX-avc1...m3u8
                        url_parts = req.url.split('/')
                        if 'playlist' in url_parts:
                            idx = url_parts.index('playlist')
                            # 钥匙就在 playlist 单词的后面一段
                            asset_id = url_parts[idx + 1]
                            break
                if asset_id: break
                time.sleep(1)

            # 3. 推送到 Worker
            if asset_id:
                print(f"🎯 提取成功! 频道: {cid} | 钥匙: {asset_id}")
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"🚀 Worker 同步状态: {res.status_code}")
            else:
                print(f"❌ {cid} 抓取失败: 未捕捉到流地址包")

            # 准备下一个频道
            del driver.requests
            
        except Exception as e:
            print(f"💥 {cid} 出错: {e}")
            
    driver.quit()
    print("🏁 全部同步任务结束")

if __name__ == "__main__":
    sync_all()
