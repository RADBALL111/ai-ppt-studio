#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎯 AI PPT 工作室 — 一键安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 需要 Python 3，请先安装: https://python.org"
    read -p "按任意键关闭..." -n 1
    exit 1
fi

echo "✅ Python $(python3 --version)"

# 安装依赖
echo "⏳ 安装依赖包（首次约1分钟）..."
pip3 install --quiet requests edge-tts python-pptx pydub numpy opencv-python anthropic moviepy 2>/dev/null

# 安装 Node（HyperFrames 需要）
if ! command -v node &>/dev/null; then
    echo "⏳ 安装 Node.js..."
    curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-darwin-arm64.tar.gz -o /tmp/node.tar.gz
    tar xzf /tmp/node.tar.gz -C /tmp/
    export PATH="/tmp/node-v22.12.0-darwin-arm64/bin:$PATH"
fi

# 检查 FFmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️ 未检测到 FFmpeg，视频渲染可能受影响"
    echo "   brew install ffmpeg"
fi

# 创建桌面快捷方式
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cat > ~/Desktop/AI\ PPT\ 工作室.command << 'SHORTCUT'
#!/bin/bash
cd "SCRIPT_PLACEHOLDER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   🎯 AI PPT 工作室"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. 📄 PPT 生成"
echo "  2. 🎬 视频生成"
echo "  3. 📋 大纲生成"
echo "  4. 🚀 一键全出"
echo ""
read -p "  选择 [1-4]: " choice
case $choice in
  1) python3 make_ppt.py ;;
  2) read -p "  选题（回车用已有大纲）: " t; [ -z "$t" ] && python3 make_video.py --storyboard output/outline.json || python3 make_video.py "$t" ;;
  3) read -p "  选题: " t; python3 ppt_outline.py ${t:+"$t"} ;;
  4) read -p "  选题: " t; python3 ppt_outline.py "$t" && python3 make_ppt.py --json output/outline.json && python3 make_video.py --storyboard output/outline.json ;;
esac
read -p "  按任意键关闭..." -n 1
SHORTCUT
sed -i '' "s|SCRIPT_PLACEHOLDER|$SCRIPT_DIR|" ~/Desktop/AI\ PPT\ 工作室.command
chmod +x ~/Desktop/AI\ PPT\ 工作室.command

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 安装完成！"
echo ""
echo "  🖥 桌面已生成: AI PPT 工作室.command"
echo "  📁 脚本目录: $SCRIPT_DIR"
echo ""
echo "  ⚠️ 使用前需配置 API Key:"
echo "     编辑 make_ppt.py 里的 DS_KEY 和 PEXELS_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "  按任意键关闭..." -n 1
