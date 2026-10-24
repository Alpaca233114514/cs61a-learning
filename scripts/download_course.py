"""Snapshot published Fall 2026 labs, homework and assigned readings.

Run with Python + lxml + reportlab. Existing files are never overwritten.
Downloaded starter code is stored, never executed.
"""
from pathlib import Path, PurePosixPath
from urllib.request import urlopen, Request
from urllib.parse import urljoin, urlsplit
from urllib.error import URLError
import time
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from html import escape
from lxml import html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://cs61a.org/fa26/'
DEST = ROOT / 'materials/fa26'
PRIVATE = ROOT / 'private/answers/fa26'
styles = getSampleStyleSheet()
pdfmetrics.registerFont(TTFont('Course', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Code', 'C:/Windows/Fonts/consola.ttf'))
for style in styles.byName.values():
    style.fontName = 'Course'
styles['Code'].fontName = 'Code'
styles['Code'].fontSize = 8
styles['Code'].leading = 10
REFRESH = False
FETCHED = {}

def replace_generated(path, data):
    """Update generated material, retaining its previous bytes in private backups."""
    if path.exists() and path.read_bytes() == data:
        return
    if path.exists():
        old = path.read_bytes()
        backup = ROOT / 'private/update-backups' / hashlib.sha256(old).hexdigest() / path.relative_to(ROOT)
        save(backup, old)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.updating')
    with temporary.open('xb') as stream:
        stream.write(data)
    temporary.replace(path)

def fetch(url):
    if url.startswith('http://'):
        url = 'https://' + url[7:]
    cache = ROOT / 'private/download-cache' / hashlib.sha256(url.encode()).hexdigest()
    if url in FETCHED:
        return FETCHED[url]
    if cache.exists() and not REFRESH:
        return cache.read_bytes()
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as response:
                data = response.read()
                replace_generated(cache, data)
                FETCHED[url] = data
                return data
        except (URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2)

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f'Refusing to overwrite: {path}')
    else:
        path.write_bytes(data)

def links(tree, base):
    return [(urljoin(base, a.get('href')), a.text_content().strip())
            for a in tree.xpath('//a[@href]')]

def pdf(tree, url, path):
    if path.exists():
        from pypdf import PdfReader
        assert len(PdfReader(path).pages) > 0
        return
    main = tree.xpath('//main | //div[@id="content"] | //div[contains(concat(" ", @class, " "), " document ")]')
    main = main[0] if main else tree
    for node in main.xpath('.//script | .//style | .//nav | .//*[contains(@class,"sidebar")]'):
        node.drop_tree()
    story = [Paragraph(escape(url), styles['Normal']), Spacer(1, 12)]
    def walk(node):
        tag = str(node.tag).lower()
        if tag in ('script', 'style', 'nav'):
            return
        if tag == 'img':
            src = node.get('src')
            if src:
                image_url = urljoin(url, src)
                print('Image', image_url, flush=True)
                data = fetch(image_url)
                im = Image(io.BytesIO(data))
                factor = min(480 / im.imageWidth, 580 / im.imageHeight, 1)
                im.drawWidth = im.imageWidth * factor
                im.drawHeight = im.imageHeight * factor
                story.extend([im, Spacer(1, 8)])
            return
        if tag == 'pre':
            text = node.text_content().expandtabs(4)
            story.extend([Preformatted(text, styles['Code'], maxLineLength=94), Spacer(1, 8)])
            return
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'h4', 'dt', 'dd', 'tr') and not node.xpath('.//pre | .//p | .//ul | .//ol | .//div | .//table'):
            text = ' '.join(node.text_content().split())
            if text:
                sty = styles[{'h1':'Heading1','h2':'Heading2','h3':'Heading3','h4':'Heading4'}.get(tag,'BodyText')]
                story.append(Paragraph(escape(('• ' if tag == 'li' else '') + text), sty))
            for im in node.xpath('.//img'):
                walk(im)
            return
        for child in node:
            walk(child)
    walk(main)
    path.parent.mkdir(parents=True, exist_ok=True)
    def footer(canvas, doc):
        canvas.setFont('Course', 8)
        canvas.drawString(42, 24, f'CS 61A Fall 2026 | Official source snapshot | {doc.page}')
    SimpleDocTemplate(str(path), rightMargin=42, leftMargin=42, topMargin=36, bottomMargin=40).build(story, onFirstPage=footer, onLaterPages=footer)

def main():
    home = html.fromstring(fetch(BASE))
    items = {}
    for url, title in links(home, BASE):
        if re.search(r'/fa26/(labs?/lab\d+|hw/hw\d+)/$', url):
            items[url] = 'lab' if '/lab' in url else 'hw'
        elif 'composingprograms.com/' in url and re.fullmatch(r'\d+\.\d+', title):
            items[url.split('#')[0]] = 'reading'
    records = []
    for url, kind in sorted(items.items()):
        print('Fetching', url, flush=True)
        raw = fetch(url)
        tree = html.fromstring(raw)
        slug = urlsplit(url).path.rstrip('/').split('/')[-1].removesuffix('.html')
        folder = DEST / kind / slug
        record = dict(kind=kind, url=url, title=tree.findtext('.//title'), source_sha256=hashlib.sha256(raw).hexdigest(), files=[], answers='not published')
        page_links = links(tree, url)
        for resource, label in page_links:
            if resource.endswith('.zip') and urlsplit(resource).netloc == 'cs61a.org' and 'sol' not in resource.lower():
                data = fetch(resource)
                record['starter_url'] = resource
                record['starter_sha256'] = hashlib.sha256(data).hexdigest()
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        name = PurePosixPath(member.filename)
                        if name.is_absolute() or '..' in name.parts or '\\' in member.filename or ':' in member.filename:
                            raise ValueError('Unsafe zip member')
                        parts = name.parts[1:] if name.parts[0] == slug else name.parts
                        relative = Path(*parts)
                        target = (PRIVATE / slug if re.search(r'(solution|answer|soln)', str(relative), re.I) else folder / 'code') / relative
                        save(target, archive.read(member))
                        record['files'].append(str(target.relative_to(ROOT)).replace('\\','/'))
                break
        output = folder / (slug + '.pdf')
        pdf(tree, url, output)
        record['pdf'] = output.relative_to(ROOT).as_posix()
        record['pdf_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
        if kind != 'reading':
            solutions = [u for u, label in page_links if re.search(r'solution|solutions|解答', label, re.I) and urlsplit(u).netloc == 'cs61a.org']
            # Older course sites publish solutions at /sol_<slug>/; do not guess answers.
            for solution in dict.fromkeys(solutions):
                solution_tree = html.fromstring(fetch(solution))
                answer_path = PRIVATE / slug / 'solutions.pdf'
                pdf(solution_tree, solution, answer_path)
                record['answers'] = answer_path.relative_to(ROOT).as_posix()
        records.append(record)
    payload = dict(source=BASE, retrieved_at=datetime.now(timezone.utc).isoformat(), scope='Only published assignment and Reading links on the Fall 2026 home page; later weeks are not published yet.', records=records)
    save(DEST / 'manifest.json', (json.dumps(payload, ensure_ascii=False, indent=2)+'\n').encode())
    save(PRIVATE / 'README.md', b'Official solutions are stored here only when publicly linked by the assignment page. No answers were generated. This entire directory is ignored by Git.\n')
    print('DONE', len(records), 'PDFs', flush=True)

if __name__ == '__main__':
    main()
