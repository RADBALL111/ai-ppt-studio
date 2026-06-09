#!/usr/bin/env python3
"""
ppt_outline.py — PPT 主题大纲生成系统
独立于视频渲染，专注内容策划。输出可直接喂给 make_video.py

模式:
  python3 ppt_outline.py                    交互模式（输入主题→生成→编辑→确认）
  python3 ppt_outline.py "选题"             快速生成
  python3 ppt_outline.py --from-url URL     从文章/网页提取大纲
  python3 ppt_outline.py --expand outline.json  将大纲展开为完整逐页脚本
"""
import os, json, re, sys, requests, hashlib, time

# ==================== 配置 ====================
try:
    from config import DS_KEY as DS_API_KEY
except ImportError:
    DS_API_KEY = "sk-你的Key"
DS_BASE = "https://api.deepseek.com"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== API ====================
def ask_structured(system, user, max_t=3000):
    headers = {"Authorization": f"Bearer {DS_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": system},
               {"role": "user", "content": user}], "max_tokens": max_t,
               "response_format": {"type": "json_object"}, "temperature": 0.7}
    for attempt in range(4):
        try:
            r = requests.post(f"{DS_BASE}/v1/chat/completions", headers=headers, json=payload, timeout=90)
            data = r.json()
            if "choices" not in data:
                print(f"  ⚠️ API 返回异常: {str(data)[:100]}")
                time.sleep(3 * (attempt + 1))
                continue
            content = data["choices"][0]["message"]["content"]
            if not content or content.strip() in ("", "{}", "[]"):
                time.sleep(2); continue
            return json.loads(content)
        except Exception as e:
            if attempt == 3: raise
            print(f"  ⚠️ 重试 {attempt+1}/3: {str(e)[:60]}")
            time.sleep(3 * (attempt + 1))

def ask_text(prompt, max_t=800):
    headers = {"Authorization": f"Bearer {DS_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_t}
    r = requests.post(f"{DS_BASE}/v1/chat/completions", headers=headers, json=payload, timeout=30)
    return r.json()["choices"][0]["message"]["content"].strip()

# ==================== 大纲模板库 ====================
OUTLINE_TEMPLATES = {
    "冲击反转": {
        "structure": "钩子→反常识→数据→解释→新视角→行动→金句",
        "style": "快节奏、强冲突、每页大字",
        "适合": "短视频口播、抖音/B站、争议话题"
    },
    "故事叙事": {
        "structure": "场景→人物→困境→转折→领悟→升华",
        "style": "画面感、情感共鸣、留白",
        "适合": "品牌故事、个人IP、情感类"
    },
    "干货教程": {
        "structure": "问题→原因→方法1→方法2→方法3→总结",
        "style": "清晰、结构化、每页一个方法",
        "适合": "知识付费、教学、How-to"
    },
    "数据说服": {
        "structure": "核心数字→对比→原因→影响→方案→预期",
        "style": "数据驱动、KPI大字、理性",
        "适合": "商业汇报、投资人Pitch、年终总结"
    },
    "产品发布": {
        "structure": "痛点→现有方案缺陷→我们的方案→核心功能→效果→CTA",
        "style": "极简、大图、一句一页",
        "适合": "新品发布、Demo Day、众筹"
    },
    "观点评论": {
        "structure": "事件→主流观点→我的立场→论据1→论据2→反方反驳→结论",
        "style": "逻辑严密、引用数据、金句收尾",
        "适合": "热点评论、行业分析、观点输出"
    },
}

# ==================== 大纲生成 ====================
OUTLINE_PROMPT = """你是顶级内容策划师。根据选题生成 PPT 大纲。请输出JSON。

## 可用模板
{templates}

## 输出格式
{{
  "topic": "选题",
  "template": "选用的模板名",
  "angle": "切入角度（一句话）",
  "target_audience": "目标受众",
  "tone": "语气（冲击/理性/温情/幽默）",
  "outline": [
    {{"section": "板块标题", "key_message": "核心信息", "bullet_points": ["要点1","要点2"], "suggested_visual": "建议画面/图片关键词"}}
  ],
  "hook": "开头钩子（15字以内）",
  "closing": "结尾金句（20字以内）",
  "estimated_pages": 数字
}}

## 要求
- 5-8 个板块，每板块 2-4 个要点
- 每个要点 15 字以内
- suggested_visual 是英文关键词（供搜图用）
- 开头必须有冲突或反常识"""

def generate_outline(topic, template_name=None):
    """生成 PPT 主题大纲"""
    # 列出可用模板
    template_list = "\n".join(f"- {k}: {v['structure']} (适合{v['适合']})"
                             for k, v in OUTLINE_TEMPLATES.items())

    if template_name and template_name in OUTLINE_TEMPLATES:
        template_hint = f"\n优先使用「{template_name}」模板。"
    else:
        template_hint = "\n根据选题自动选择最合适的模板。"

    user_msg = f"选题：{topic}{template_hint}\n\n请输出JSON格式的大纲。"
    result = ask_structured(
        OUTLINE_PROMPT.replace("{templates}", template_list),
        user_msg, 3000
    )
    return result

# ==================== 大纲展开 ====================
EXPAND_PROMPT = """你是短视频脚本写手。将 PPT 大纲展开为逐页脚本。请输出JSON。

## 输出JSON格式
{{
  "storyboard": [
    {{"layout":"hero|statement|split_col|quote_slide|kpi_bold",
      "rhythm":"hero|non-hero",
      "title":"≤15字文案",
      "subtitle":"补充说明≤25字",
      "highlight":"2-6字关键词",
      "image_query":"英文搜图关键词"
    }}
  ]
}}

## 规则
- hero/non-hero 必须交替
- 前3页建立冲突或悬念
- 禁止鸡汤废话
- 每页 highlight 用于搜图和视觉强调"""

def expand_to_storyboard(outline):
    """将大纲展开为逐页分镜脚本（可直接喂 make_video.py）"""
    result = ask_structured(EXPAND_PROMPT,
        f"大纲：{json.dumps(outline, ensure_ascii=False)}", 4000)
    return result.get("storyboard", [])

# ==================== 大纲优化 ====================
def refine_outline(outline, feedback):
    """根据用户反馈优化大纲"""
    result = ask_structured(
        "你是内容策划师。根据用户反馈修改大纲。请输出JSON。",
        f"原始大纲：{json.dumps(outline, ensure_ascii=False)}\n\n用户反馈：{feedback}\n\n请输出修改后的完整大纲JSON",
        3000
    )
    return result

# ==================== 从 URL 提取大纲 ====================
def outline_from_url(url):
    """从文章/网页提取核心观点生成大纲"""
    prompt = f"""从以下网页内容提取核心观点，生成 PPT 大纲。

网页URL: {url}

请先总结文章核心内容，再生成大纲。如果无法访问URL，请说明。
输出JSON格式：{{"topic":"...","angle":"...","outline":[...]}}"""

    result = ask_structured("你是内容摘要师。从网页提取观点。请输出JSON。", prompt + "\n请输出JSON格式", 2000)
    return result

# ==================== 交互模式 ====================
def interactive():
    """交互式大纲生成"""
    print("=" * 55)
    print("PPT 大纲生成器 — 交互模式")
    print("=" * 55)

    # 1. 输入主题
    topic = input("\n📌 请输入选题（如：为什么越省钱越穷）: ").strip()
    if not topic:
        topic = ask_text("给我一个爆款选题，15字以内")
        print(f"  AI 选题: {topic}")

    # 2. 选模板
    print("\n📋 可用模板:")
    for i, (name, info) in enumerate(OUTLINE_TEMPLATES.items(), 1):
        print(f"  {i}. {name} — {info['适合']}")
    choice = input(f"\n  选模板 (1-{len(OUTLINE_TEMPLATES)}，回车自动): ").strip()
    template = list(OUTLINE_TEMPLATES.keys())[int(choice)-1] if choice.isdigit() else None

    # 3. 生成大纲
    print("\n⏳ 生成大纲...")
    outline = generate_outline(topic, template)

    # 4. 展示
    _print_outline(outline)

    # 5. 编辑循环
    while True:
        action = input("\n🔧 [a]接受并展开 [e]编辑反馈 [r]重生成 [t]换模板 [q]退出: ").strip().lower()
        if action == 'a':
            break
        elif action == 'e':
            feedback = input("  修改意见（如：第二段太弱、加数据、语气太硬）: ").strip()
            if feedback:
                print("  ⏳ 优化中...")
                outline = refine_outline(outline, feedback)
                _print_outline(outline)
        elif action == 'r':
            print("  ⏳ 重新生成...")
            outline = generate_outline(topic, template)
            _print_outline(outline)
        elif action == 't':
            print("\n📋 模板:")
            for i, (name, info) in enumerate(OUTLINE_TEMPLATES.items(), 1):
                print(f"  {i}. {name}")
            c = input("  选模板: ").strip()
            if c.isdigit():
                template = list(OUTLINE_TEMPLATES.keys())[int(c)-1]
                outline = generate_outline(topic, template)
                _print_outline(outline)
        elif action == 'q':
            print("已退出。大纲已自动保存。")
            _save(outline)
            return

    # 6. 展开为脚本
    print("\n⏳ 展开为逐页分镜脚本...")
    storyboard = expand_to_storyboard(outline)
    print(f"  ✅ {len(storyboard)} 页分镜脚本")

    # 7. 保存
    output = {"outline": outline, "storyboard": storyboard}
    path = _save(output)
    print(f"\n✅ 已保存: {path}")
    print(f"  下一步: python3 make_video.py --storyboard {path}")
    return output


def _print_outline(outline):
    print(f"\n{'='*50}")
    print(f"📌 {outline.get('topic','')}")
    print(f"  🎯 角度: {outline.get('angle','')}")
    print(f"  👥 受众: {outline.get('target_audience','')}")
    print(f"  🗣  语气: {outline.get('tone','')} | 模板: {outline.get('template','')}")
    print(f"  🪝 钩子: {outline.get('hook','')}")
    print(f"{'='*50}")
    for i, sec in enumerate(outline.get("outline", []), 1):
        print(f"\n  {i}. {sec.get('section','')}")
        print(f"     💡 {sec.get('key_message','')}")
        for bp in sec.get("bullet_points", []):
            print(f"       • {bp}")
    print(f"\n  🔚 结尾: {outline.get('closing','')}")
    print(f"  📄 预计 {outline.get('estimated_pages','?')} 页")

def _save(data):
    path = os.path.join(OUTPUT_DIR, "outline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

# ==================== 主入口 ====================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--expand" and len(sys.argv) > 2:
            # 展开已有大纲
            with open(sys.argv[2]) as f:
                outline = json.load(f)
            storyboard = expand_to_storyboard(outline.get("outline", outline))
            print(json.dumps({"storyboard": storyboard}, ensure_ascii=False, indent=2))
        elif arg == "--from-url" and len(sys.argv) > 2:
            outline = outline_from_url(sys.argv[2])
            _print_outline(outline)
            _save(outline)
        elif arg == "--templates":
            for name, info in OUTLINE_TEMPLATES.items():
                print(f"\n{name}: {info['structure']}\n  适合: {info['适合']}")
        else:
            # 快速模式
            topic = " ".join(sys.argv[1:])
            print(f"📌 {topic}")
            outline = generate_outline(topic)
            _print_outline(outline)
            storyboard = expand_to_storyboard(outline)
            _save({"outline": outline, "storyboard": storyboard})
            print(f"\n✅ {len(storyboard)} 页 · 已保存 output/outline.json")
    else:
        interactive()
