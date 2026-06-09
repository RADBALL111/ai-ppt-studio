#!/usr/bin/env python3
"""
AI PPT 工作室 — 手机版 Web 服务
部署后手机浏览器打开即用，电脑熄屏也能跑（云端部署）
"""
import os, sys, json, subprocess, glob, time, threading
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 导入核心逻辑
sys.path.insert(0, os.path.dirname(__file__))
try:
    from make_ppt import generate_outline, print_outline, expand_to_storyboard, make_ppt_from_storyboard
    HAS_LOCAL = True
except:
    HAS_LOCAL = False

HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>AI PPT 工作室</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f0f1a;color:#fff;min-height:100vh;padding:16px}
h1{font-size:24px;text-align:center;margin:16px 0 8px;background:linear-gradient(135deg,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{text-align:center;color:#888;font-size:14px;margin-bottom:24px}
.card{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:16px}
.card h2{font-size:18px;margin-bottom:12px;color:#00ff88}
input,select,button{width:100%;padding:14px;border-radius:10px;border:none;font-size:16px;margin-bottom:10px}
input,select{background:#0f0f23;color:#fff;border:1px solid #333}
select{-webkit-appearance:none}
button{background:linear-gradient(135deg,#00ff88,#00cc66);color:#000;font-weight:700;cursor:pointer}
button:active{opacity:.8}
.btn-outline{background:transparent;border:1px solid #00ff88;color:#00ff88}
.log{background:#0a0a15;border-radius:10px;padding:14px;font-size:13px;color:#aaa;max-height:200px;overflow-y:auto;white-space:pre-wrap;font-family:monospace}
.result{background:#1a2a1a;border:1px solid #00ff8844;border-radius:10px;padding:16px;margin-top:12px}
.result a{color:#00ff88;display:block;padding:6px 0;text-decoration:none;font-size:15px}
.spinner{display:none;text-align:center;padding:20px;color:#00ff88}
.spinner.show{display:block}
@keyframes spin{to{transform:rotate(360deg)}}
.spin{display:inline-block;animation:spin 1s linear infinite;font-size:24px}
.tabs{display:flex;gap:8px;margin-bottom:16px}
.tab{flex:1;text-align:center;padding:10px;border-radius:8px;background:#1a1a2e;color:#888;cursor:pointer;font-size:13px}
.tab.active{background:#00ff8822;color:#00ff88;border:1px solid #00ff8844}
</style>
</head>
<body>
<h1>🎯 AI PPT 工作室</h1>
<p class="sub">手机浏览器一键生成 PPT 和视频</p>

<div class="tabs">
  <div class="tab active" onclick="switchTab('ppt')">📄 PPT</div>
  <div class="tab" onclick="switchTab('video')">🎬 视频</div>
  <div class="tab" onclick="switchTab('all')">🚀 一键全出</div>
</div>

<div class="card">
  <input id="topic" placeholder="📌 输入选题，如：为什么越省钱越穷" autofocus>
  <button onclick="generate()">⚡ 开始生成</button>
  <div class="spinner" id="spinner"><span class="spin">⏳</span> 生成中...</div>
  <div class="log" id="log"></div>
  <div id="results"></div>
</div>

<script>
let mode='ppt';
function switchTab(m){mode=m;document.querySelectorAll('.tab').forEach((t,i)=>{
  t.classList.toggle('active',(i==0&&m=='ppt')||(i==1&&m=='video')||(i==2&&m=='all'));});}

async function generate(){
  const topic=document.getElementById('topic').value.trim();
  if(!topic){alert('请输入选题');return}
  document.getElementById('spinner').classList.add('show');
  document.getElementById('log').textContent='⏳ '+{ppt:'生成PPT',video:'生成视频',all:'全流程'}[mode]+'...';
  document.getElementById('results').innerHTML='';

  try{
    const r=await fetch('/generate',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic,mode})
    });
    const data=await r.json();
    document.getElementById('log').textContent=data.log||'完成';
    if(data.files){
      let html='<div class="result"><h3>✅ 生成完成</h3>';
      data.files.forEach(f=>{html+=`<a href="/download/${f.name}" download>📥 ${f.label} (${f.size})</a>`});
      html+='</div>';
      document.getElementById('results').innerHTML=html;
    }
  }catch(e){
    document.getElementById('log').textContent='❌ 错误: '+e.message;
  }
  document.getElementById('spinner').classList.remove('show');
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get('topic', '').strip()
    mode = data.get('mode', 'ppt')

    log_lines = [f"📌 {topic}"]

    try:
        if mode == 'ppt':
            subprocess.run([sys.executable, "make_ppt.py", "--quick", topic],
                          cwd=os.path.dirname(__file__), timeout=300, capture_output=True)
        elif mode == 'video':
            subprocess.run([sys.executable, "make_video.py", topic],
                          cwd=os.path.dirname(__file__), timeout=300, capture_output=True)
        else:  # all
            subprocess.run([sys.executable, "ppt_outline.py", topic],
                          cwd=os.path.dirname(__file__), timeout=120, capture_output=True)
            subprocess.run([sys.executable, "make_ppt.py", "--json", "output/outline.json"],
                          cwd=os.path.dirname(__file__), timeout=180, capture_output=True)
            subprocess.run([sys.executable, "make_video.py", "--storyboard", "output/outline.json"],
                          cwd=os.path.dirname(__file__), timeout=300, capture_output=True)

        # 收集产出文件
        files = []
        for name, label in [("slides.html", "🌐 HTML 幻灯片"), ("slides.pptx", "📄 PPTX 文件")]:
            path = os.path.join(OUTPUT_DIR, name)
            if os.path.exists(path):
                files.append({"name": name, "label": label,
                             "size": f"{os.path.getsize(path)/1024:.0f}KB"})

        videos = sorted(glob.glob(os.path.join(OUTPUT_DIR, "slides_proj/renders/*.mp4")))
        if videos:
            v = videos[-1]
            files.append({"name": os.path.relpath(v, OUTPUT_DIR), "label": "🎬 视频 MP4",
                         "size": f"{os.path.getsize(v)/1024/1024:.1f}MB"})

        log_lines.append(f"✅ 完成！{len(files)} 个文件")
        return jsonify({"log": "\n".join(log_lines), "files": files})
    except Exception as e:
        return jsonify({"log": f"❌ {e}", "files": []})

@app.route('/download/<path:filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "文件不存在", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7890))
    print(f"\n🎯 手机访问: http://你的IP:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
