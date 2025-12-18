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
    options.add_argument('--window-size=1920,1080') # 必须设为标准高清，确保中心点坐标准确
    # 深度伪装：让网站认为这是普通浏览器
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 这里的 driver 使用 selenium-wire 增强版
    driver = webdriver.Chrome(options=options)
    # 移除 webdriver 标识
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def sync_all():
    print(f"⏰ 任务启动: {time.strftime('%H:%M:%S')}")
    driver = get_driver()
    
    for cid in CHANNELS:
        print(f"🔍 正在尝试抓取频道: {cid}")
        try:
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 1. 初步等待加载
            time.sleep(10)
            
            # 2. 模拟点击播放器中心（模拟真实用户交互）
            try:
                # 点击屏幕中心坐标 (960, 540)
                driver.execute_script("document.elementFromPoint(960, 540).click();")
                print(f"🖱️  已发送点击指令...")
            except Exception as e:
                print(f"⚠️  点击失败(可能已自动播放): {e}")

            # 3. 轮询扫描流量包 (最长等待 20 秒)
            asset_id = None
            found = False
            for i in range(20):
                for req in driver.requests:
                    if 'master.m3u8' in req.url:
                        # 找到包含 AssetID 的路径段
                        parts = req.url.split('/')
                        # 典型的 URL: .../playlist/ASSET_ID/master.m3u8
                        if 'playlist' in parts:
                            idx = parts.index('playlist')
                            asset_id = parts[idx + 1]
                            found = True
                            break
                if found: break
                time.sleep(1)
            
            # 4. 上传结果
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 成功! ID: {asset_id} | Worker响应: {res.status_code}")
            else:
                print(f"❌ {cid} 抓取失败: 在流量中未发现 master.m3u8")

            # 每次抓取后清理请求记录，防止干扰下一个频道
            del driver.requests
            
        except Exception as e:
            print(f"💥 {cid} 运行崩溃: {e}")
            
    driver.quit()
    print("🏁 所有任务处理完毕")

if __name__ == "__main__":
    sync_all()
