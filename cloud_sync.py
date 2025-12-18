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

    chromedriver_autoinstaller.install()

    

    # 获取环境变量中的代理（由 Workflow 提供）

    proxy = os.getenv("HTTP_PROXY", "http://127.0.0.1:7890")

    

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

    options.add_argument('--window-size=1920,1080')

    # 模拟真实设备

    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    

    return webdriver.Chrome(options=options, seleniumwire_options=sw_options)



def sync():

    driver = get_driver()

    # 验证 IP 是否成功变成台湾 (可选测试)

    try:

        driver.get("https://ifconfig.me/ip")

        print(f"当前出口 IP: {driver.page_source}")

    except: pass



    for cid in CHANNELS:

        try:

            print(f"正在抓取: {cid}")

            driver.get(f"https://www.ofiii.com/channel/watch/{cid}")

            time.sleep(15) 

            

            # 点击播放器中心

            driver.execute_script("document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).click();")

            

            asset_id = None

            for req in driver.requests:

                if cid in req.url and '.m3u8' in req.url:

                    parts = req.url.split('/')

                    if 'playlist' in parts:

                        asset_id = parts[parts.index('playlist') + 1]

                        break

            

            if asset_id:

                requests.post(WORKER_URL, json={"id": cid, "key": asset_id, "pw": AUTH_PW})

                print(f"✅ {cid} 同步成功: {asset_id}")

            else:

                print(f"❌ {cid} 失败")

            del driver.requests

        except Exception as e:

            print(f"💥 {cid} 异常: {e}")

    driver.quit()



if __name__ == "__main__":

    sync()
