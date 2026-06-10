"""云端版 — 密码保护 + PPT 生成"""
import os, json, re, random, time, requests
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)
try: from config import DS_KEY, PEXELS_KEY
except: DS_KEY = os.environ.get("DS_KEY",""); PEXELS_KEY = os.environ.get("PEXELS_KEY","")

PASSWORD = "ppt666"
W, H = 1920, 1080
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/images", exist_ok=True)

# ========== API ==========
def ask_json(system, user, max_t=2000):
    for attempt in range(3):
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DS_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"system","content":system},
                      {"role":"user","content":user}],"max_tokens":max_t,"response_format":{"type":"json_object"}},
                timeout=60)
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except: time.sleep(1)
    return {}

def fetch_image(keyword, index):
    has_cjk = any('一' <= c <= '鿿' for c in keyword)
    params = {"query": keyword, "per_page": 1, "orientation": "landscape"}
    if has_cjk: params["locale"] = "zh-CN"
    try:
        r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": PEXELS_KEY}, params=params, timeout=8)
        if "photos" in r.json() and r.json()["photos"]:
            url = r.json()["photos"][0]["src"]["large"]
            img = requests.get(url, timeout=10).content
            path = f"{OUTPUT_DIR}/images/img_{index}.jpg"
            with open(path, "wb") as f: f.write(img)
            return path
    except: pass
    return None

# ========== 分镜 ==========
PROMPT = """你是短视频导演。生成6-8页分镜。请输出JSON。
规则：hero/non-hero交替、禁鸡汤、highlight用2-6字、每句≤15字
layout: hero / statement / split_col / quote_slide / kpi_bold
示例: [{"layout":"hero","rhythm":"hero","title":"工资涨了","subtitle":"物价涨更快","highlight":"陷阱"}]
输出JSON:{"storyboard":[...]}"""

def gen_storyboard(topic):
    for _ in range(2):
        try:
            r = ask_json(PROMPT, f"选题：{topic}\n输出JSON", 2000)
            sb = r.get("storyboard",[])
            if isinstance(sb,list) and len(sb)>=3: return sb
        except: continue
    return [{"layout":"hero","rhythm":"hero","title":topic,"subtitle":"","highlight":"核心"}]*5

# ========== 主题 ==========
THEMES = {
    "swiss":{"--bg":"#1a1a1a","--card":"#2a2a2a","--accent":"#FFE600","--accent2":"#fff","--text":"#f0f0f0","--textDim":"#999","--fontTitle":"900","--radius":"0px","--grid":"swiss"},
    "editorial":{"--bg":"#fcfaf7","--card":"#fff","--accent":"#8b0000","--accent2":"#333","--text":"#1a1a1a","--textDim":"#777","--fontTitle":"900","--radius":"0px","--grid":"editorial"},
    "cyber":{"--bg":"#0a0a1a","--card":"#1a1a3e","--accent":"#00ff88","--accent2":"#00cc66","--text":"#e0e0ff","--textDim":"#a0a0cc","--fontTitle":"900","--radius":"8px","--grid":"none"},
    "white":{"--bg":"#fff","--card":"#f5f5f5","--accent":"#111","--accent2":"#666","--text":"#111","--textDim":"#888","--fontTitle":"700","--radius":"4px","--grid":"none"},
    "bold":{"--bg":"#000","--card":"#0f0f0f","--accent":"#FF4500","--accent2":"#FFD700","--text":"#fff","--textDim":"#aaa","--fontTitle":"900","--radius":"0px","--grid":"none"},
    "tokyo":{"--bg":"#1a1b2e","--card":"#252740","--accent":"#ff9e64","--accent2":"#e0894f","--text":"#c0caf5","--textDim":"#6c7096","--fontTitle":"900","--radius":"8px","--grid":"none"},
}

# ========== HTML ==========
def build_html(storyboard, ds, images):
    is_swiss = ds.get("--grid") == "swiss"
    slides, anis = [], []; t = 0
    for i, s in enumerate(storyboard):
        layout = s.get("layout","statement"); title = s.get("title",""); sub = s.get("subtitle",""); hl = s.get("highlight","")
        dur = 2.5 * (1.6 if layout in ("hero","cover") else 1.0); sid = f"s{i}"
        has_img = i in images
        img_bg = f'<div class="img-bg" style="background-image:url(images/img_{i}.jpg)"></div><div class="img-overlay"></div>' if has_img else ""
        if is_swiss and layout == "hero":
            body = f'<div class="swiss-hero"><div class="accent-bar"></div><h1>{title}</h1><p class="lead">{sub}</p><div class="tag">{hl}</div></div>'
        elif is_swiss and layout == "quote_slide":
            body = f'<div class="swiss-quote"><div class="rule"></div><blockquote>{title}</blockquote><cite>{hl}</cite></div>'
        elif is_swiss and layout == "kpi_bold":
            body = f'<div class="swiss-kpi"><span class="num">{hl}</span><span class="title">{title}</span><span class="desc">{sub}</span></div>'
        else:
            body = f'<h2 id="{sid}_t">{title}</h2><p id="{sid}_s">{sub}</p><div id="{sid}_h" class="tag">{hl}</div>'
        anis.append(f'tl.from("#{sid}",{{opacity:0,y:30,duration:0.7}},{t:.1f});')
        slides.append(f'<section id="{sid}" class="slide{ " has-img" if has_img else ""}" data-start="{t:.1f}" data-duration="{dur:.1f}">{img_bg}<div class="slide-inner">{body}</div></section>')
        t += dur
    css_vars = "\n".join(f"    {k}: {v};" for k,v in ds.items())
    return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width={W},height={H}">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script><style>
:root{{{css_vars}--w:{W}px;--h:{H}px;--margin:80px;--fs-hero:clamp(72px,10vw,130px);--fs-h1:clamp(56px,7vw,100px);--fs-h2:clamp(42px,5vw,72px);--fs-body:clamp(22px,2.5vw,36px);--font-sans:"PingFang SC","Hiragino Sans GB",sans-serif;--font-display:"Georgia",serif}}
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:var(--w);height:var(--h);overflow:hidden;background:var(--bg);font-family:var(--font-sans);color:var(--text)}}
.slide{{position:absolute;top:0;left:0;width:var(--w);height:var(--h);display:flex;align-items:center;justify-content:center;flex-direction:column;z-index:1}}
h1{{font-family:var(--font-display);font-size:var(--fs-h1);font-weight:var(--fontTitle)}}h2{{font-size:var(--fs-h2);font-weight:var(--fontTitle)}}
.tag{{display:inline-block;background:var(--accent);color:var(--bg);font-size:22px;font-weight:800;padding:6px 22px;border-radius:2px;margin-bottom:24px}}
.swiss-hero h1{{font-size:var(--fs-hero);font-weight:900;line-height:1.08}}.swiss-hero .lead{{font-size:var(--fs-body);color:var(--textDim);margin-top:24px}}
.accent-bar{{position:absolute;top:0;left:0;width:1px;height:100%;background:var(--accent)}}
.swiss-quote{{text-align:left;width:1600px;padding:0 120px}}.swiss-quote .rule{{width:80px;height:1px;background:var(--accent);margin-bottom:40px}}
.swiss-quote blockquote{{font-family:var(--font-display);font-size:var(--fs-h2);font-weight:700}}
.swiss-kpi{{display:flex;flex-direction:column;align-items:center;gap:12px}}.swiss-kpi .num{{font-size:180px;font-weight:900;color:var(--accent)}}
.img-bg{{position:absolute;top:0;left:0;width:100%;height:100%;background-size:cover;background-position:center;z-index:0;filter:brightness(0.55)}}
.img-overlay{{position:absolute;top:0;left:0;width:100%;height:100%;background:linear-gradient(180deg,rgba(0,0,0,0.3),rgba(0,0,0,0.65));z-index:0}}
.has-img .slide-inner{{position:relative;z-index:1;text-shadow:0 2px 20px rgba(0,0,0,0.5)}}
</style></head><body><div data-composition-id="main" data-start="0" data-duration="{t:.1f}" data-width="{W}" data-height="{H}">{chr(10).join(slides)}</div>
<script>window.__timelines={{}};const tl=gsap.timeline({{paused:true}});{chr(10).join(anis)}window.__timelines["main"]=tl</script></body></html>'''

# ========== Web UI ==========
PAGE = '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI PPT</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,sans-serif;background:#0a0a15;color:#fff;min-height:100vh;padding:20px}
h1{font-size:24px;text-align:center;margin:16px 0;background:linear-gradient(135deg,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.card{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:16px}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #333;background:#0f0f23;color:#fff;font-size:16px;margin-bottom:10px}
button{width:100%;padding:14px;border-radius:10px;border:none;font-size:18px;font-weight:700;background:linear-gradient(135deg,#00ff88,#00cc66);color:#000;cursor:pointer}
.log{background:#0a0a16;border-radius:10px;padding:14px;font-size:13px;color:#aaa;max-height:200px;overflow-y:auto;white-space:pre-wrap;margin-top:10px}
.result{margin-top:12px}.result a{display:block;padding:8px;color:#00ff88;text-decoration:none}
.lock{text-align:center;padding:40px 20px}.lock input{width:200px;text-align:center;margin:0 auto;display:block}
</style></head><body>
<h1>🎯 AI PPT 工作室</h1>
<div id="lock" class="card lock"><p style="color:#aaa;margin-bottom:12px">🔐 输入密码</p><input id="pwd" type="password" placeholder="密码" autofocus><button onclick="unlock()">进入</button></div>
<div id="app" style="display:none"><div class="card"><input id="topic" placeholder="📌 输入选题，如：为什么越省钱越穷"><button onclick="gen()">⚡ 生成 PPT</button><div class="log" id="log"></div><div id="res"></div></div></div>
<script>
const PWD=''' + json.dumps(PASSWORD) + ''';
function unlock(){if(document.getElementById('pwd').value===PWD){document.getElementById('lock').style.display='none';document.getElementById('app').style.display='block'}else{alert('密码错误')}}
async function gen(){const t=document.getElementById('topic').value.trim();if(!t)return;document.getElementById('log').textContent='⏳ 生成中...';const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:t,pwd:PWD})});const d=await r.json();document.getElementById('log').textContent=d.log||'完成';if(d.files){let h='';d.files.forEach(f=>{h+=`<a href="/download/${f.name}" download>📥 ${f.label} (${f.size})</a>`});document.getElementById('res').innerHTML=h}}
</script></body></html>'''

@app.route('/')
def index(): return PAGE

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    if data.get('pwd','') != PASSWORD: return {"log":"❌ 密码错误","files":[]}
    topic = data.get('topic','').strip()
    try:
        storyboard = gen_storyboard(topic)
        images = {}
        for i, s in enumerate(storyboard[:6]):
            kw = s.get("highlight","") or s.get("title","")[:8]
            path = fetch_image(kw, i)
            if path: images[i] = path; time.sleep(0.2)
        theme = random.choice(list(THEMES.keys()))
        html = build_html(storyboard, THEMES[theme], images)
        with open(f"{OUTPUT_DIR}/slides.html","w") as f: f.write(html)
        files = [{"name":"slides.html","label":"🌐 HTML 幻灯片","size":f"{os.path.getsize(f'{OUTPUT_DIR}/slides.html')//1024}KB"}]
        return {"log":f"✅ {topic}\n{len(storyboard)} 页 | {theme} | {len(images)} 张图","files":files}
    except Exception as e:
        return {"log":f"❌ {e}","files":[]}

@app.route('/download/<path:filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    return send_file(path, as_attachment=True) if os.path.exists(path) else ("Not found",404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',7890)))
