"""Check downloaded files, PDF text, and Git answer exclusions without running coursework."""
from pathlib import Path
import json
import hashlib
import subprocess
from pypdf import PdfReader
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'materials/fa26/manifest.json').read_text(encoding='utf8'))
lines = ['# CS 61A · Fall 2026', '', '来源：https://cs61a.org/fa26/；下载时间：' + manifest['retrieved_at'], '',
         '仅包含当前官网已发布的 Lab 0–2、HW 1–3、Reading 1.1–1.7。后续周次尚未发布，未混入往年资料。', '',
         'PDF 为官方网页的静态排版阅读版，代码保留官网原始起始文件。动态图和交互演示请访问来源网页。', '',
         '未发现作业页面链接的公开官方答案；未生成答案。日后答案放入 `private/answers/fa26/`，已被 Git 忽略。', '',
         '| 类型 | 资料 | 来源 |', '| --- | --- | --- |']
pages = 0
for item in manifest['records']:
    path = ROOT / item['pdf']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['pdf_sha256']
    doc = PdfReader(path)
    assert all(len(p.extract_text().strip()) > 30 for p in doc.pages)
    pages += len(doc.pages)
    source = ROOT / 'private/download-cache' / hashlib.sha256(item['url'].encode()).hexdigest()
    tree = html.fromstring(source.read_bytes())
    hidden = tree.xpath('//*[contains(@class,"solution") or contains(@class,"answer") or contains(@id,"solution") or contains(@id,"answer")]')
    print(item['kind'], path.stem, len(doc.pages), 'pages; answer elements:', [(x.tag,x.get('class'),x.get('id')) for x in hidden])
    rel = path.relative_to(ROOT / 'materials/fa26').as_posix()
    lines.append(f"| {item['kind']} | [{item['title']}]({rel}) | [官网]({item['url']}) |")
assert subprocess.run(['git','check-ignore','-q','private/answers/fa26/check.py'], cwd=ROOT).returncode == 0
assert subprocess.run(['git','check-ignore','-q','materials/fa26/hw/hw01/code/hw01.py'], cwd=ROOT).returncode == 1
index = ROOT / 'materials/fa26/README.md'
if not index.exists():
    index.write_text('\n'.join(lines)+'\n',encoding='utf8')
print('Verified',len(manifest['records']),'PDFs;',pages,'pages; answer ignore and starter tracking OK')
