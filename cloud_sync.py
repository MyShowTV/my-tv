import os
import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# ====== 配置区 ======
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666" 

CHANNELS = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]

def get_driver():
    # 修复 Errno 111：下载驱动时先临时关闭环境变量代理（GitHub 环境直连极快）
    old_http = os.environ.pop('HTTP_PROXY', None)
    old_https = os.environ.pop('HTTPS_PROXY', None)
    
    print("📥 正在安装浏览器驱动...")
    chromedriver_autoinstaller.install()
    
    # 还原代理环境变量，确保后续 Selenium 请求走代理
    if old_http: os.environ['HTTP_PROXY'] = old_http
    if old_https: os.environ['HTTPS_PROXY'] = old_https
    
    proxy = "http://127.0.0.1:7890"
    sw_options = {
        'proxy': {
            'http': proxy,
            'https': proxy,
            'no_proxy': 'localhost,127.0.0.1'
        },
        'connection_timeout': 30
    }
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print("🚀 启动抓取流程...")
    driver = get_driver()

    for cid in CHANNELS:
        try:
            print(f"📡 目标频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 给网页足够的加载时间
            time.sleep(25) 
            
            # 点击页面中心
            driver.execute_script("document.elementFromPoint(960, 540).click();")
            
            asset_id = None
            for req in driver.requests:
                if cid in req.url and '.m3u8' in req.url:
                    parts = req.url.split('/')
                    if 'playlist' in parts:
                        asset_id = parts[parts.index('playlist') + 1]
                        break
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ 同步成功 | 钥匙: {asset_id} | Worker响应: {res.status_code}")
            else:
                print(f"❌ 失败: 未捕获到流地址，请检查台湾节点是否在线")
            
            del driver.requests
            
        except Exception as e:
            print(f"💥 运行异常: {e}")

    driver.quit()
    print("🏁 任务完成")

if __name__ == "__main__":
    sync()
