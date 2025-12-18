import requests
import os

# 成都台发号器接口
CHANNELS = {
    "成都新闻综合": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv1high/CDTV1High.flv/playlist.m3u8",
    "成都经济资讯": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv2high/CDTV2High.flv/playlist.m3u8",
    "成都都市生活": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv3high/CDTV3High.flv/playlist.m3u8",
    "成都影视文艺": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv4high/CDTV4High.flv/playlist.m3u8",
    "成都公共": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv5high/CDTV5High.flv/playlist.m3u8",
    "成都少儿": "https://www.cditv.cn/live/getLiveUrl?url=https://cdn1.cditv.cn/cdtv6high/CDTV6High.flv/playlist.m3u8",
    "龙华电影": "https://cdi.ofiii.com/ocean/video/playlist/-2zcqx6V66M/litv-longturn03-avc1_2936000=4-mp4a_114000=2.m3u8",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.cditv.cn/"
}

def fetch_real_url(api_url):
    """访问发号器接口，提取 data.url 中的真实 m3u8"""
    try:
        res = requests.get(api_url, headers=HEADERS, timeout=10)
        data = res.json()

        # 真实地址在 data.url
        if "data" in data and isinstance(data["data"], dict):
            real_url = data["data"].get("url")
            if real_url and real_url.startswith("http"):
                return real_url

        return None

    except Exception as e:
        print("请求失败:", e)
        return None


def main():
    m3u_file = "TWTV.m3u"

    if not os.path.exists(m3u_file):
        print("错误：找不到 TWTV.m3u 文件")
        return

    with open(m3u_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    updated = 0
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]
        new_lines.append(line)

        for name, api_url in CHANNELS.items():
            if f'tvg-name="{name}"' in line or line.strip().endswith(f",{name}"):

                print(f"\n正在更新：{name}")
                real_url = fetch_real_url(api_url)

                if real_url:
                    print(f"✅ 成功：{real_url}")
                    new_lines.append(real_url + "\n")
                    updated += 1
                else:
                    print("❌ 失败，保留旧地址")
                    new_lines.append(lines[i+1])

                i += 1
                break

        i += 1

    with open(m3u_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"\n✅ 更新完成，共更新 {updated} 个频道")


if __name__ == "__main__":
    main()
