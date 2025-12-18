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
    # 1. 核心修复：清理所有可能干扰 Selenium 通信的环境变量
    for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(env_var, None)
    
    print("📥 正在初始化浏览器驱动...")
    chromedriver_autoinstaller.install()
    
    proxy_addr = "127.0.0.1:7890"
    
    # 2. Selenium-Wire 配置：只代理外部请求，排除本地回环
    sw_options = {
        'proxy': {
            'http': f'http://{proxy_addr}',
            'https': f'http://{proxy_addr}',
            'no_proxy': 'localhost,127.0.0.1' 
        },
        'verify_ssl': False,
        'auto_config': False
    }
    
    # 3. Chrome 参数配置
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 强制浏览器内核走代理访问网页
    options.add_argument(f'--proxy-server=http://{proxy_addr}')
    # 强制排除本地地址，防止 Errno 111
    options.add_argument("--proxy-bypass-list=localhost;127.0.0.1;*.local")
    
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print("🚀 开始抓取流程...")
    driver = get_driver()
    
    # 验证浏览器内的实际出口 IP
    try:
        driver.get("https://ifconfig.me/ip")
        print(f"🕵️ 浏览器实际出口 IP: {driver.page_source.strip()}")
    except Exception as e:
        print(f"⚠️ 无法验证 IP: {e}")

    for cid in CHANNELS:
        try:
            print(f"📡 正在处理: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 等待播放器数据包加载
            time.sleep(35) 
            
            asset_id = None
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
                print(f"✅ {cid} 成功 -> {asset_id} (Worker: {res.status_code})")
            else:
                print(f"❌ {cid} 失败: 未嗅探到 m3u8 地址包")
            
            del driver.requests
        except Exception as e:
            print(f"💥 {cid} 异常: {e}")
    
    driver.quit()
    print("🏁 任务全部完成")

if __name__ == "__main__":
    sync()
