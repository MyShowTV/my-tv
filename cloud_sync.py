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
    # 1. 环境清理，确保下载驱动直连
    for env_var in ['HTTP_PROXY', 'HTTPS_PROXY']:
        os.environ.pop(env_var, None)
    
    chromedriver_autoinstaller.install()
    
    # 2. 重新锁定代理地址
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
    # 核心：强制 Chrome 进程级别使用代理
    options.add_argument(f'--proxy-server=http://{proxy_addr}')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print("🚀 启动深度抓取流程...")
    driver = get_driver()
    
    # 再次确认浏览器内的 IP
    try:
        driver.get("https://ifconfig.me/ip")
        print(f"🕵️ 浏览器内核出口 IP: {driver.page_source.strip()}")
    except: pass

    for cid in CHANNELS:
        try:
            print(f"📡 正在嗅探频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 等待视频流加载
            time.sleep(30) 
            
            asset_id = None
            # 强化匹配规则
            for req in driver.requests:
                u = req.url
                if 'playlist' in u and (cid in u or 'litv' in u):
                    try:
                        # 典型的 URL 结构: .../playlist/ASSET_ID/index.m3u8
                        parts = u.split('/')
                        idx = parts.index('playlist')
                        asset_id = parts[idx + 1]
                        break
                    except: continue
            
            if asset_id:
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 同步成功: {asset_id}")
            else:
                print(f"❌ {cid} 抓取失败 (未发现数据包)")
            
            del driver.requests # 清理内存防止 GitHub 报错
        except Exception as e:
            print(f"💥 {cid} 异常: {e}")
    
    driver.quit()

if __name__ == "__main__":
    sync()
