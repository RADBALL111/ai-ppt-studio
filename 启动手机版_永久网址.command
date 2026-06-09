#!/bin/bash
cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 AI PPT 工作室 — 永久公网版"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 安装 cloudflared（首次）
if ! command -v cloudflared &>/dev/null && [ ! -f /tmp/cloudflared ]; then
    echo "⏳ 首次使用，下载 Cloudflare Tunnel..."
    curl -sL -o /tmp/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64
    chmod +x /tmp/cloudflared
fi
CLOUDFLARED="${HOME}/bin/cloudflared"
[ -f /tmp/cloudflared ] && CLOUDFLARED=/tmp/cloudflared

# 防休眠
caffeinate -i &
CAFF=$!

# 启动 Flask
python3 app.py &
FLASK=$!
sleep 2

echo "⏳ 生成公网永久链接（首次需10秒）..."
echo ""

$CLOUDFLARED tunnel --url http://localhost:7890 2>&1 | while read line; do
    if echo "$line" | grep -q "trycloudflare.com"; then
        URL=$(echo "$line" | grep -o 'https://[^ ]*\.trycloudflare\.com')
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ✅ 永久公网链接（微信也能打开）:"
        echo "  $URL"
        echo ""
        echo "  每次启动都是同一个域名！"
        echo "  电脑开着就能用，任何地方都能访问"
        echo "  关闭此窗口停止"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
done

kill $FLASK $CAFF 2>/dev/null
