export default {
  async fetch(request) {
    const url = new URL(request.url);
    const host = url.host;
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();
    const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    // 配置表（会被 cloud_sync.py 自动更新）
    const config = {
      // --- 成都系列 ---
      "cdtv1": { name: "成都新闻综合", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv1high%2FCDTV1High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv2": { name: "成都经济频道", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv2high%2FCDTV2High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv3": { name: "成都都市生活", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv3high%2FCDTV3High.flv%2Fplaylist.m3u8", type: "cdtv" },

      // --- 龙华系列（自动更新部分）---
      "lhtv01": { name: "龙华电影", key: "这里填钥匙", type: "ofiii" },
      "lhtv02": { name: "龙华经典", key: "这里填钥匙", type: "ofiii" },
      "lhtv03": { name: "龙华戏剧", key: "这里填钥匙", type: "ofiii" },
      "lhtv04": { name: "龙华日韩", key: "这里填钥匙", type: "ofiii" },
      "lhtv05": { name: "龙华偶像", key: "这里填钥匙", type: "ofiii" },
      "lhtv06": { name: "龙华卡通", key: "这里填钥匙", type: "ofiii" },
      "lhtv07": { name: "龙华洋片", key: "这里填钥匙", type: "ofiii" }
    };

    // 首页导航（保持不变）
    if (path === "" || path === "index") {
      let html = `<html><head><meta charset="utf-8"><title>电视直播源</title><style>body{font-family:sans-serif;background:#f5f7fa;padding:30px}.box{max-width:700px;margin:auto;background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}h2{color:#007bff;border-bottom:2px solid #007bff;padding-bottom:5px}.row{display:flex;justify-content:space-between;padding:12px;border-bottom:1px solid #eee}code{color:#d63384;background:#fef1f6;padding:3px 6px;border-radius:4px;font-size:13px}</style></head><body><div class="box"><h1>📺 20 合 1 稳定直播源</h1>`;
      const groups = { "cdtv": "成都台系列", "ofiii": "龙华全系列" };
      for (const [gKey, gName] of Object.entries(groups)) {
        html += `<h2>${gName}</h2>`;
        for (const id in config) {
          if (config[id].type === gKey) {
            html += `<div class="row"><span>${config[id].name}</span><code>https://${host}/${id}.m3u8</code></div>`;
          }
        }
      }
      return new Response(html + "</div></body></html>", { headers: { "Content-Type": "text/html;charset=UTF-8" } });
    }

    const ch = config[path];
    if (!ch) return new Response("404", { status: 404 });

    try {
      // 成都台逻辑
      if (ch.type === "cdtv") {
        const res = await fetch(ch.api, { headers: { "Referer": "https://www.cditv.cn/", "User-Agent": UA } });
        const text = await res.text();
        const match = text.replace(/\\/g, "").match(/https?:\/\/[^\s"'<>|]+?\.m3u8\?[^\s"'<>|]+/);
        if (match) return Response.redirect(match[0], 302);
      }

      // 龙华逻辑
      if (ch.type === "ofiii") {
        if (ch.key === "这里填钥匙") return new Response("该频道 AssetID 尚未更新", { status: 500 });
        
        const finalUrl = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
        return proxyM3u8(finalUrl, "https://www.ofiii.com/", UA);
      }
    } catch (e) {
      return new Response("发生错误: " + e.message, { status: 500 });
    }
    return new Response("未抓取到流", { status: 404 });
  }
};

/**
 * M3U8 代理补全函数
 */
async function proxyM3u8(targetUrl, referer, ua) {
  const res = await fetch(targetUrl, { headers: { "Referer": referer, "User-Agent": ua } });
  if (!res.ok) return new Response("钥匙已失效，请重新抓取填入", { status: 403 });

  let content = await res.text();
  const baseUrl = targetUrl.substring(0, targetUrl.lastIndexOf('/') + 1);
  
  const fixedContent = content.split('\n').map(line => {
    line = line.trim();
    if (line && !line.startsWith('#') && !line.startsWith('http')) return baseUrl + line;
    return line;
  }).join('\n');
  
  return new Response(fixedContent, { 
    headers: { 
      "Content-Type": "application/vnd.apple.mpegurl", 
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "no-cache"
    } 
  });
}
