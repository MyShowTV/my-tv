import os
import requests
import time
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options

# ====== 你的 Worker 生产配置 ======
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666" # ！！！请确保与 Worker 代码里的密码一致 ！！！

CHANNELS = [
    "litv-longturn03", "litv-longturn21", "litv-longturn18", 
    "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"
]

def get_driver():
    chromedriver_autoinstaller.install()
    
    # 强制指定使用 GitHub 虚拟机中 Clash 开启的 7890 代理端口
    proxy = "http://127.0.0.1:7890"
    
    sw_options = {
        'proxy': {
            'http': proxy,
            'https': proxy,
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 移除自动化标记，防止被 Ofiii 检测
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)

def sync():
    print(f"🚀 任务启动，准备通过代理抓取 Ofiii...")
    driver = get_driver()

    for cid in CHANNELS:
        try:
            print(f"🔍 正在抓取频道: {cid}")
            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
            
            # 等待播放器和 JS 脚本加载完毕（台湾节点延迟可能较高，给足 20 秒）
            time.sleep(20) 
            
            # 模拟点击页面中心激活播放流
            driver.execute_script("document.elementFromPoint(960, 540).click();")
            
            asset_id = None
            # 扫描捕获到的所有网络请求
            for req in driver.requests:
                if cid in req.url and '.m3u8' in req.url:
                    parts = req.url.split('/')
                    if 'playlist' in parts:
                        asset_id = parts[parts.index('playlist') + 1]
                        break
            
            if asset_id:
                # 将钥匙推送到你的 Cloudflare Worker
                res = requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW}, timeout=10)
                print(f"✅ {cid} 同步成功! 钥匙: {asset_id} (Worker 响应: {res.status_code})")
            else:
                print(f"❌ {cid} 失败: 未能捕捉到 m3u8 数据包，请检查机场台湾节点是否可用")
            
            # 清理当前请求记录，准备抓取下一个频道
            del driver.requests
            
        except Exception as e:
            print(f"💥 {cid} 抓取过程中发生异常: {e}")

    driver.quit()
    print("🏁 所有同步任务处理完毕")

if __name__ == "__main__":
    sync()
