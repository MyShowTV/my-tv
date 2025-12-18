import os
import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# ====== 你的 Worker 配置 ======
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666" 
CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]

def get_driver():
    # 环境隔离：下载驱动不走代理
    old_http = os.environ.pop('HTTP_PROXY', None)
    old_https = os.environ.pop('HTTPS_PROXY', None)
    
    chromedriver_autoinstaller.install()
    
    # 还原代理环境变量
    if old_http: os.environ['HTTP_PROXY'] = old_http
    if old_https: os.environ['HTTPS_PROXY'] = old_https
    
    proxy_addr = "127.0.0.1:7890"
    
    sw_options = {
        'proxy': {
            'http': f'http://{proxy_addr}',
            'https': f'http://{proxy_addr}',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--proxy-server=http://{proxy_addr}')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print("🚀 任务启动...")
    driver = get_driver()
    
    # 验证浏览器内的出口 IP
    try:
        driver.get("https://ifconfig.me/ip")
        print(f"🕵️ 浏览器内核出口 IP: {driver.page_source.strip()}")
    except: pass

    for cid in CHANNELS:
        try:
            print(f"📡 正在尝试抓取: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 给页面加载留出充足时间（30秒）
            time.sleep(30) 
            
            asset_id = None
            # 扫描所有包含 playlist 关键字的 m3u8 请求
            for req in driver.requests:
                u = req.url
                if 'playlist' in u and (cid in u or 'litv' in u):
                    try:
                        parts = u.split('/')
                        asset_id = parts[parts.index('playlist') + 1]
                        break
                    except: continue
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 同步成功: {asset_id}")
            else:
                print(f"❌ {cid} 失败: 未捕获到流地址包")
            
            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 发生异常: {e}")
    
    driver.quit()
    print("🏁 所有任务处理完毕")

if __name__ == "__main__":
    sync()
