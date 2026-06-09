#!/bin/bash
cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📱 AI PPT 工作室 — 手机版"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 防休眠
caffeinate -i &
CAFF=$!

# 启动 Flask
python3 app.py &
sleep 2

# 公网隧道
echo "⏳ 生成公网链接..."
npx localtunnel --port 7890 2>&1 | while read line; do
  if echo "$line" | grep -q "your url is:"; then
    URL=$(echo "$line" | grep -o 'https://[^ ]*\.loca\.lt')
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ 手机打开（微信可开）:"
    echo "  $URL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  fi
done

kill $CAFF 2>/dev/null
