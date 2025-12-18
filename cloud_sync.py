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
    # 彻底隔离驱动下载，防止干扰
    old_proxy = os.environ.get('HTTP_PROXY')
    if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
    if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']
    
    chromedriver_autoinstaller.install()
    
    # 重新设置代理
    os.environ['HTTP_PROXY'] = "http://127.0.0.1:7890"
    os.environ['HTTPS_PROXY'] = "http://127.0.0.1:7890"

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
            'no_proxy': 'localhost,127.0.0.1'
        },
        'auto_config': False, # 强制手动配置代理
        'request_storage': 'memory'
    }
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    driver = get_driver()
    # 强制测试驱动内部的 IP
    try:
        driver.get("https://ifconfig.me/ip")
        print(f"🕵️ 浏览器实际出口 IP: {driver.page_source.strip()}")
    except: pass

    for cid in CHANNELS:
        try:
            print(f"📡 抓取频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 增加等待时间，Ofiii 节点较慢
            time.sleep(30) 
            
            asset_id = None
            # 扩大搜索范围：只要包含 playlist 且在 ofiii 的请求中
            for req in driver.requests:
                url = req.url
                if 'playlist' in url and (cid in url or 'litv' in url):
                    # 尝试多种分割方式获取 ID
                    try:
                        parts = url.split('/')
                        asset_id = parts[parts.index('playlist') + 1]
                        break
                    except: continue
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 同步成功: {asset_id}")
            else:
                print(f"❌ {cid} 失败 (未捕获到 playlist 请求)")
            
            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 异常: {e}")
    
    driver.quit()

if __name__ == "__main__":
    sync()
