from flask import Flask
app = Flask(__name__)

HTML = '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>已关闭</title>
<style>body{font-family:-apple-system,sans-serif;background:#0a0a15;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center}
h1{font-size:48px;color:#ff4444}p{color:#888;margin-top:16px}</style></head><body><div><h1>⛔ 服务已关闭</h1><p>请使用桌面版：AI PPT 工作室.command</p></div></body></html>'''

@app.route('/')
@app.route('/<path:path>')
def offline(path=None):
    return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT',7890)))
