export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();

    // --- 处理 Python 脚本发来的更新请求 ---
    if (request.method === "POST" && path === "update_key") {
      try {
        const data = await request.json();
        // 这里可以扩展：将抓到的 key 存入 KV 数据库，实现真正全自动
        console.log(`收到更新请求: 频道 ${data.id}, 新 Key ${data.key}`);
        return new Response("OK", { status: 200 });
      } catch (e) {
        return new Response("Error", { status: 400 });
      }
    }

    const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    // 1. 配置表
    const config = {
      "cdtv1": { name: "成都新闻", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv1high%2FCDTV1High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "lhtv01": { name: "龙华电影", key: "ztAK5EHzPGE", type: "ofiii" },
      // ... 其他频道保持一致
    };

    // 首页导航逻辑 (略，保持你原有的 HTML)
    if (path === "" || path === "index") { /* ... 原有逻辑 ... */ }

    const ch = config[path];
    if (!ch) return new Response("404", { status: 404 });

    // 2. 龙华逻辑：Master 代理补全
    if (ch.type === "ofiii") {
      const finalUrl = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
      return proxyM3u8(finalUrl, "https://www.ofiii.com/", UA);
    }

    // 3. 成都台逻辑 (略，保持你原有的逻辑)
  }
};

async function proxyM3u8(targetUrl, referer, ua) {
  const res = await fetch(targetUrl, { headers: { "Referer": referer, "User-Agent": ua } });
  if (!res.ok) return new Response("Key Expired", { status: 403 });

  let content = await res.text();
  const baseUrl = targetUrl.substring(0, targetUrl.lastIndexOf('/') + 1);
  
  const fixedContent = content.split('\n').map(line => {
    line = line.trim();
    if (line && !line.startsWith('#') && !line.startsWith('http')) return baseUrl + line;
    return line;
  }).join('\n');
  
  return new Response(fixedContent, { 
    headers: { "Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*" } 
  });
}
