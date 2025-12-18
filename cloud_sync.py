import time
import requests
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# --- 配置区 (请务必填对密码) ---
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "你的Workers认证密码" 
PROXY = "127.0.0.1:7890"

CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]

def get_driver():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--proxy-server=http://{PROXY}')
    
    sw_options = {
        'proxy': {
            'http': f'http://{PROXY}',
            'https': f'http://{PROXY}',
        },
        'verify_ssl': False 
    }
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def main():
    driver = get_driver()
    print("🚀 启动抓取脚本...")
    
    for cid in CHANNELS:
        try:
            print(f"正在抓取: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 给页面留出足够的加载时间 (代理环境较慢)
            time.sleep(45) 
            
            asset_id = None
            # 逆向搜索 m3u8
            for req in reversed(driver.requests):
                if req.response and 'index.m3u8' in req.url:
                    asset_id = req.url.split('/')[-2]
                    break
            
            if asset_id:
                # 提交数据
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ 成功: {cid} -> {asset_id} (响应: {res.status_code})")
            else:
                print(f"❌ 失败: {cid} 未找到 m3u8 (页面标题: {driver.title})")
                
            del driver.requests
        except Exception as e:
            print(f"💥 频道 {cid} 发生致命错误: {e}")

    driver.quit()

if __name__ == "__main__":
    main()
