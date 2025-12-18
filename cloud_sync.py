import os
import requests
import time
import json
from seleniumwire import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 配置项可单独提取，方便修改
WORKER_URL = "https://cdtv-proxy.leixinghuazj.workers.dev/update_key"
AUTH_PW = "your_password_666"
CHANNELS = ["litv-longturn03", "litv-longturn21", "litv-longturn18", "litv-longturn11", "litv-longturn12", "litv-longturn01", "litv-longturn02"]
PROXY = "127.0.0.1:7890"  # Mihomo代理端口
# 可选：是否强制校验台湾IP（设为False可跳过校验，测试抓取逻辑）
FORCE_TW_CHECK = False

def get_driver():
    # 【关键修改】保留代理环境变量，让selenium和requests都能走代理
    # 若需要强制走代理，可手动设置环境变量
    os.environ['HTTP_PROXY'] = f'http://{PROXY}'
    os.environ['HTTPS_PROXY'] = f'http://{PROXY}'
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,*.local'

    # 自动安装Chrome驱动
    chromedriver_autoinstaller.install()

    # Selenium Wire代理配置
    sw_options = {
        'proxy': {
            'http': f'http://{PROXY}',
            'https': f'http://{PROXY}',
            'no_proxy': 'localhost,127.0.0.1,*.local'
        },
        'verify_ssl': False,
        'disable_encoding': True  # 解决部分m3u8请求编码问题
    }

    # Chrome浏览器配置
    options = Options()
    # 无头模式（GitHub Actions必须）
    options.add_argument('--headless=new')  # 新版headless，兼容性更好
    options.add_argument('--no-sandbox')  # 解决Linux环境的沙箱限制
    options.add_argument('--disable-dev-shm-usage')  # 解决内存不足问题
    options.add_argument(f'--proxy-server=http://{PROXY}')  # Chrome代理
    options.add_argument("--proxy-bypass-list=localhost;127.0.0.1;*.local")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # 模拟正常浏览器UA
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 初始化驱动
    driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
    # 设置页面加载超时
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    return driver

def get_asset_id(driver, cid):
    """单独提取asset_id抓取逻辑，便于复用和调试"""
    asset_id = None
    # 遍历所有请求（反向遍历，取最新的m3u8请求）
    for req in reversed(driver.requests):
        # 过滤m3u8请求（放宽条件，避免漏抓）
        if req.method == 'GET' and 'playlist' in req.url and 'index.m3u8' in req.url:
            try:
                # 分割URL获取asset_id（兼容不同URL格式）
                url_parts = req.url.split('/')
                # 找到index.m3u8的上一级目录作为asset_id
                m3u8_index = url_parts.index('index.m3u8') if 'index.m3u8' in url_parts else -1
                if m3u8_index > 0:
                    asset_id = url_parts[m3u8_index - 1]
                # 验证asset_id是否有效（非空且长度合理）
                if asset_id and 5 < len(asset_id) < 50:  # 合理的长度范围
                    break
                else:
                    asset_id = None
            except Exception as e:
                print(f"⚠️ 解析asset_id失败: {e}")
                continue
    return asset_id

def sync():
    driver = None
    try:
        driver = get_driver()
        print("✅ 浏览器驱动初始化成功")

        # 地区二次校验（可选关闭）
        if FORCE_TW_CHECK:
            try:
                print("🔍 校验浏览器出口IP...")
                driver.get("http://ip-api.com/json/")
                # 等待页面加载完成，获取pre标签内容
                pre_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "pre"))
                )
                data = json.loads(pre_element.text)
                ip = data.get('query', 'UNKNOWN')
                country_code = data.get('countryCode', 'UNKNOWN')
                print(f"🕵️ 浏览器实际出口: {ip} ({country_code})")
                if country_code != 'TW':
                    print("🛑 非台湾 IP，根据版权保护机制停止抓取。")
                    return
            except Exception as e:
                print(f"⚠️ IP校验失败: {e}")
                # 若校验失败且强制校验，直接终止
                if FORCE_TW_CHECK:
                    return
        else:
            print("ℹ️ 已跳过台湾IP校验")

        # 遍历频道抓取
        for cid in CHANNELS:
            try:
                print(f"\n📡 开始抓取频道: {cid}")
                # 清空之前的请求记录
                del driver.requests
                # 访问频道页面
                driver.get(f"https://www.ofiii.com/channel/watch/{cid}")
                # 等待流加载（动态等待，最长60秒，每2秒检查一次请求）
                wait_time = 0
                max_wait = 60
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    # 检查是否出现m3u8请求
                    has_m3u8 = any('playlist' in req.url and 'index.m3u8' in req.url for req in driver.requests)
                    if has_m3u8:
                        print(f"⌛ 频道{cid}已加载出m3u8流，停止等待（耗时{wait_time}秒）")
                        break
                if wait_time >= max_wait:
                    print(f"❌ 频道{cid}超时未加载出m3u8流")
                    continue

                # 抓取asset_id
                asset_id = get_asset_id(driver, cid)
                if asset_id:
                    # 提交到Worker
                    try:
                        res = requests.post(
                            WORKER_URL,
                            json={"id": cid, "key": asset_id, "pw": AUTH_PW},
                            timeout=15,
                            # requests也走代理
                            proxies={
                                'http': f'http://{PROXY}',
                                'https': f'http://{PROXY}'
                            }
                        )
                        res.raise_for_status()  # 抛出HTTP错误
                        print(f"✅ 频道{cid}提交成功 -> asset_id: {asset_id} (Worker状态码: {res.status_code})")
                    except requests.exceptions.RequestException as e:
                        print(f"❌ 频道{cid}提交失败: {e}")
                else:
                    print(f"❌ 频道{cid}未捕获到asset_id")

            except Exception as e:
                print(f"💥 频道{cid}处理出错: {e}")
                continue

    except Exception as e:
        print(f"🚨 全局错误: {e}")
    finally:
        # 确保浏览器关闭
        if driver:
            driver.quit()
            print("\n🔌 浏览器已关闭")
    print("\n🏁 任务完成")

if __name__ == "__main__":
    sync()
