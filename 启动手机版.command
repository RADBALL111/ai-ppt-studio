#!/bin/bash
cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📱 AI PPT 工作室 — 手机版"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 防止电脑休眠（合盖也能跑）
caffeinate -i &
CAFFEINE=$!
echo "✅ 电脑不会休眠"

# 启动服务
python3 app.py &
FLASK=$!
sleep 2

# 获取本机 IP
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📱 手机浏览器打开:"
echo "  http://$IP:7890"
echo ""
echo "  （手机和电脑需在同一WiFi）"
echo ""
echo "  关闭此窗口停止服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 保持运行
wait $FLASK
kill $CAFFEINE 2>/dev/null
