#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙华频道 AssetID 自动抓取和更新脚本
需要在台湾代理环境下运行
"""

import os
import sys
import json
import time
import re
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LonghuaAssetFetcher:
    """龙华频道 AssetID 抓取器"""
    
    def __init__(self, use_proxy=True):
        """
        初始化抓取器
        
        Args:
            use_proxy: 是否使用代理
        """
        self.use_proxy = use_proxy
        self.base_url = "https://www.ofiii.com/"
        self.session = requests.Session()
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.ofiii.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 频道配置（与 Workers 代码中的配置对应）
        self.channels = {
            'lhtv01': {'name': '龙华电影', 'url_slug': 'movie'},
            'lhtv02': {'name': '龙华经典', 'url_slug': 'classic'},
            'lhtv03': {'name': '龙华戏剧', 'url_slug': 'drama'},
            'lhtv04': {'name': '龙华日韩', 'url_slug': 'japan-korea'},
            'lhtv05': {'name': '龙华偶像', 'url_slug': 'idol'},
            'lhtv06': {'name': '龙华卡通', 'url_slug': 'cartoon'},
            'lhtv07': {'name': '龙华洋片', 'url_slug': 'foreign'},
        }
        
        # 设置代理（如果启用）
        if self.use_proxy and os.environ.get('HTTPS_PROXY'):
            proxy = os.environ.get('HTTPS_PROXY', os.environ.get('HTTP_PROXY'))
            if proxy:
                self.session.proxies = {
                    'http': proxy,
                    'https': proxy
                }
                logger.info(f"使用代理: {proxy}")
    
    def setup_chrome_driver(self):
        """设置 Chrome 浏览器驱动"""
        chrome_options = Options()
        
        # 无头模式（无 GUI）
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 伪装成正常浏览器
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-lang=zh-TW,zh;q=0.9')
        
        # 禁用图片加载，提高速度
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 不加载图片
                'javascript': 1,  # 启用 JavaScript
            }
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # 设置代理（如果启用）
        if self.use_proxy and os.environ.get('HTTPS_PROXY'):
            proxy = os.environ.get('HTTPS_PROXY', os.environ.get('HTTP_PROXY'))
            if proxy:
                # 解析代理 URL
                parsed_proxy = urlparse(proxy)
                proxy_address = f"{parsed_proxy.hostname}:{parsed_proxy.port}"
                chrome_options.add_argument(f'--proxy-server={proxy_address}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"初始化 Chrome 驱动失败: {e}")
            return None
    
    def fetch_assetid_with_requests(self, channel_slug):
        """
        使用 requests 尝试抓取 AssetID（更快速）
        
        Args:
            channel_slug: 频道URL后缀
            
        Returns:
            AssetID 或 None
        """
        try:
            # 构造频道页面 URL
            url = f"{self.base_url}channel/{channel_slug}"
            logger.info(f"请求频道页面: {url}")
            
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # 在页面中查找 AssetID
            content = response.text
            
            # 模式1: 在 JavaScript 中查找
            patterns = [
                r'assetId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'playlist/([^/]+)/master\.m3u8',
                r'video/playlist/([^/]+)/master',
                r'"([a-zA-Z0-9]{10,})"',  # 长字符串可能是 AssetID
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # 过滤出可能的 AssetID（长度通常为 10-20 位）
                    for match in matches:
                        if 10 <= len(match) <= 20 and match.isalnum():
                            logger.info(f"找到可能的 AssetID (模式): {match[:10]}...")
                            return match
            
            logger.warning(f"未在页面中找到 AssetID")
            return None
            
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析页面失败: {e}")
            return None
    
    def fetch_assetid_with_selenium(self, channel_slug):
        """
        使用 Selenium 抓取 AssetID（更准确，但较慢）
        
        Args:
            channel_slug: 频道URL后缀
            
        Returns:
            AssetID 或 None
        """
        driver = self.setup_chrome_driver()
        if not driver:
            return None
        
        try:
            url = f"{self.base_url}channel/{channel_slug}"
            logger.info(f"使用 Selenium 访问: {url}")
            
            driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 尝试找到播放器相关元素
            asset_id = None
            
            # 方法1: 检查网络请求
            try:
                performance_log = driver.get_log('performance')
                for entry in performance_log:
                    try:
                        message = json.loads(entry['message'])
                        url = message.get('message', {}).get('params', {}).get('request', {}).get('url', '')
                        if 'playlist' in url and 'master.m3u8' in url:
                            match = re.search(r'playlist/([^/]+)/master\.m3u8', url)
                            if match:
                                asset_id = match.group(1)
                                logger.info(f"从网络请求找到 AssetID: {asset_id}")
                                break
                    except:
                        continue
            except:
                pass
            
            # 方法2: 检查页面源码
            if not asset_id:
                page_source = driver.page_source
                patterns = [
                    r'assetId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'playlist/([^/]+)/master\.m3u8',
                    r'"([a-zA-Z0-9]{10,})"',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, page_source)
                    for match in matches:
                        if 10 <= len(match) <= 20 and match.isalnum():
                            asset_id = match
                            logger.info(f"从页面源码找到 AssetID: {asset_id}")
                            break
            
            return asset_id
            
        except TimeoutException:
            logger.error("页面加载超时")
            return None
        except WebDriverException as e:
            logger.error(f"WebDriver 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return None
        finally:
            driver.quit()
    
    def fetch_all_channels(self):
        """抓取所有频道的 AssetID"""
        results = {}
        
        logger.info("开始抓取所有龙华频道...")
        
        for channel_id, channel_info in self.channels.items():
            logger.info(f"处理频道: {channel_info['name']}")
            
            # 先用 requests 尝试（更快）
            asset_id = self.fetch_assetid_with_requests(channel_info['url_slug'])
            
            # 如果没找到，用 Selenium 尝试（更准确）
            if not asset_id:
                logger.info(f"requests 未找到，尝试使用 Selenium...")
                asset_id = self.fetch_assetid_with_selenium(channel_info['url_slug'])
            
            if asset_id:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'key': asset_id,
                    'type': 'ofiii',
                    'timestamp': int(time.time())
                }
                logger.info(f"✅ {channel_info['name']}: 找到 AssetID - {asset_id[:10]}...")
            else:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'key': '这里填钥匙',  # 保持原样
                    'type': 'ofiii',
                    'timestamp': int(time.time()),
                    'error': '未找到 AssetID'
                }
                logger.warning(f"❌ {channel_info['name']}: 未找到 AssetID")
            
            # 避免请求过快
            time.sleep(2)
        
        return results
    
    def update_worker_config(self, results):
        """
        更新 Cloudflare Workers 配置文件
        
        Args:
            results: 抓取结果
            
        Returns:
            是否成功更新
        """
        try:
            # 读取现有的 Workers 代码
            worker_file = "workers.js"
            if not os.path.exists(worker_file):
                logger.error(f"找不到 Workers 文件: {worker_file}")
                return False
            
            with open(worker_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新每个频道的 key
            updated = False
            for channel_id, channel_data in results.items():
                if channel_data.get('key') and channel_data['key'] != '这里填钥匙':
                    # 查找并替换 key
                    pattern = rf'"{channel_id}":\s*{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]+"'
                    replacement = f'"{channel_id}": {{ name: "{channel_data["name"]}", key: "{channel_data["key"]}"'
                    
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        updated = True
                        logger.info(f"已更新 {channel_data['name']} 的配置")
            
            if updated:
                # 备份原文件
                backup_file = f"workers.js.backup.{int(time.time())}"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(open(worker_file, 'r', encoding='utf-8').read())
                
                # 写入新文件
                with open(worker_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"✅ Workers 配置已更新")
                return True
            else:
                logger.info("⚠️ 没有需要更新的配置")
                return False
                
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def save_results_json(self, results):
        """保存结果到 JSON 文件"""
        try:
            timestamp = int(time.time())
            filename = f"longhua_assets_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'channels': results
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return None
    
    def test_proxy_connection(self):
        """测试代理连接是否正常"""
        try:
            test_url = "http://ip-api.com/json/"
            response = self.session.get(test_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                country = data.get('countryCode', 'Unknown')
                ip = data.get('query', 'Unknown')
                logger.info(f"代理测试成功 - IP: {ip}, 国家: {country}")
                return country == 'TW'
            return False
        except Exception as e:
            logger.error(f"代理测试失败: {e}")
            return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("龙华频道 AssetID 同步脚本开始运行")
    logger.info("=" * 60)
    
    # 检查是否在代理环境下
    use_proxy = True
    if os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY'):
        logger.info("检测到代理设置")
    else:
        logger.warning("未检测到代理设置，可能无法访问龙华网站")
        use_proxy = False
    
    # 创建抓取器
    fetcher = LonghuaAssetFetcher(use_proxy=use_proxy)
    
    # 测试代理连接
    if use_proxy:
        logger.info("测试代理连接...")
        if not fetcher.test_proxy_connection():
            logger.error("❌ 代理连接测试失败，请检查代理设置")
            return False
    
    # 抓取所有频道
    results = fetcher.fetch_all_channels()
    
    # 统计结果
    success_count = sum(1 for r in results.values() if r.get('key') and r['key'] != '这里填钥匙')
    total_count = len(results)
    
    logger.info("=" * 60)
    logger.info(f"抓取完成: {success_count}/{total_count} 个频道成功")
    logger.info("=" * 60)
    
    # 保存结果
    json_file = fetcher.save_results_json(results)
    
    # 更新 Workers 配置
    if success_count > 0:
        logger.info("尝试更新 Workers 配置...")
        updated = fetcher.update_worker_config(results)
        if updated:
            logger.info("✅ 配置更新成功")
        else:
            logger.warning("⚠️ 配置未更新")
    else:
        logger.warning("⚠️ 没有找到有效的 AssetID，跳过配置更新")
    
    # 生成摘要
    logger.info("=" * 60)
    logger.info("抓取结果摘要:")
    for channel_id, data in results.items():
        status = "✅" if data.get('key') and data['key'] != '这里填钥匙' else "❌"
        key_preview = data['key'][:10] + "..." if len(data['key']) > 10 else data['key']
        logger.info(f"  {status} {data['name']}: {key_preview}")
    logger.info("=" * 60)
    
    # 如果成功抓取到至少一个频道，返回成功
    return success_count > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"脚本执行失败: {e}", exc_info=True)
        sys.exit(1)
