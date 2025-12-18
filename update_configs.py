#!/usr/bin/env python3
"""
更新 Workers 配置的辅助脚本
"""

import json
import re
import sys

def update_workers_js(config_file, workers_file="workers.js"):
    """更新 Workers 配置文件"""
    
    # 读取最新的 AssetID 配置
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 读取 Workers 代码
    with open(workers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新配置
    updated = False
    for channel_id, channel_data in data['channels'].items():
        if channel_data.get('key') and channel_data['key'] != '这里填钥匙':
            # 构建正则表达式模式
            pattern = rf'"{channel_id}":\s*{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]+"'
            replacement = f'"{channel_id}": {{ name: "{channel_data["name"]}", key: "{channel_data["key"]}"'
            
            # 替换
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                updated = True
                print(f"✅ 更新 {channel_data['name']}")
    
    if updated:
        # 备份原文件
        import time
        backup = f"{workers_file}.backup.{int(time.time())}"
        with open(backup, 'w', encoding='utf-8') as f:
            with open(workers_file, 'r', encoding='utf-8') as original:
                f.write(original.read())
        
        # 写入新文件
        with open(workers_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Workers 配置已更新")
        return True
    
    print("⚠️ 没有需要更新的配置")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python update_configs.py <config_json_file>")
        sys.exit(1)
    
    update_workers_js(sys.argv[1])
