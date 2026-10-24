"""CS61A command: refresh published course material without overwriting exercises."""
import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


def discover(course, raw):
    items = {}
    for url, title in course.links(course.html.fromstring(raw), course.BASE):
        if re.search(r'/fa26/(labs?/lab\d+|hw/hw\d+)/$', url) and urlsplit(url).netloc == 'cs61a.org':
            items[url] = 'lab' if '/lab' in url else 'hw'
        elif urlsplit(url).netloc in ('composingprograms.com', 'www.composingprograms.com') and re.fullmatch(r'\d+\.\d+', title):
            items[url.split('#')[0]] = 'reading'
    if not items:
        raise RuntimeError('No published material found; refusing to replace the index.')
    return items


def extract_starter(course, data, folder, slug):
    files, preserved = [], []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            name = PurePosixPath(member.filename)
            if (name.is_absolute() or '..' in name.parts or '\\' in member.filename
                    or ':' in member.filename or (member.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe archive path: ' + member.filename)
            parts = name.parts[1:] if name.parts[0] == slug else name.parts
            if not parts:
                raise ValueError('Empty archive path')
            relative = Path(*parts)
            answer = re.search(r'(solution|answer|soln|(?:^|[_-])sol(?:[._-]|$))', str(relative), re.I)
            target = (course.PRIVATE / slug if answer else folder / 'code') / relative
            if not target.resolve().is_relative_to(course.ROOT.resolve()):
                raise ValueError('Archive path escaped the repository')
            content = archive.read(member)
            if target.exists() and target.read_bytes() != content:
                incoming = course.ROOT / 'private/upstream' / slug / hashlib.sha256(data).hexdigest() / relative
                course.save(incoming, content)
                preserved.append(target.relative_to(course.ROOT).as_posix())
            else:
                course.save(target, content)
            files.append(target.relative_to(course.ROOT).as_posix())
    return files, preserved


def render(course, raw, url, target):
    # Render to a fresh temporary file; replace only after successful PDF validation.
    from pypdf import PdfReader
    temp_root = course.ROOT / 'private/pdf-tmp'
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cs-pdf-', dir=temp_root) as temp:
        output = Path(temp) / 'material.pdf'
        course.pdf(course.html.fromstring(raw), url, output)
        reader = PdfReader(output)
        if not reader.pages or not all(p.extract_text().strip() for p in reader.pages):
            raise ValueError('Generated PDF has an empty page')
        course.replace_generated(target, output.read_bytes())


def update_item(course, url, kind, previous):
    raw = course.fetch(url)
    tree = course.html.fromstring(raw)
    slug = urlsplit(url).path.rstrip('/').split('/')[-1].removesuffix('.html')
    folder = course.DEST / kind / slug
    digest = hashlib.sha256(raw).hexdigest()
    record = dict(kind=kind, url=url, title=tree.findtext('.//title'), source_sha256=digest,
                  files=[], preserved_local_files=[], answers='not published')
    page_links = course.links(tree, url)
    for resource, _ in page_links:
        if resource.endswith('.zip') and urlsplit(resource).netloc == 'cs61a.org' and 'sol' not in resource.lower():
            data = course.fetch(resource)
            record['starter_url'] = resource
            record['starter_sha256'] = hashlib.sha256(data).hexdigest()
            record['files'], record['preserved_local_files'] = extract_starter(course, data, folder, slug)
            break
    target = folder / (slug + '.pdf')
    # Never put embedded solutions in a public question PDF.
    answer_nodes = tree.xpath('//*[contains(@class,"solution") or contains(@id,"solution")]')
    if answer_nodes:
        render(course, raw, url, course.PRIVATE / slug / 'with-solutions.pdf')
        for node in answer_nodes:
            if node.getparent() is not None:
                node.drop_tree()
        question_raw = course.html.tostring(tree)
        record['answers'] = (course.PRIVATE / slug / 'with-solutions.pdf').relative_to(course.ROOT).as_posix()
    else:
        question_raw = raw
    if not target.exists() or previous.get('source_sha256') != digest:
        render(course, question_raw, url, target)
    record['pdf'] = target.relative_to(course.ROOT).as_posix()
    record['pdf_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    for solution, label in page_links:
        if re.search(r'\bsolutions?\b|解答', label, re.I) and urlsplit(solution).netloc == 'cs61a.org':
            data = course.fetch(solution)
            answer_path = course.PRIVATE / slug / (hashlib.sha256(solution.encode()).hexdigest()[:10] + '.pdf')
            if data.startswith(b'%PDF-'):
                from pypdf import PdfReader
                if not PdfReader(io.BytesIO(data)).pages:
                    raise ValueError('Empty solution PDF')
                course.replace_generated(answer_path, data)
            else:
                render(course, data, solution, answer_path)
            record['answers'] = answer_path.relative_to(course.ROOT).as_posix()
    return record


def update(course):
    course.REFRESH = True
    course.FETCHED.clear()
    manifest_path = course.DEST / 'manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf8')) if manifest_path.exists() else {}
    records = {r['url']: r for r in old.get('records', [])}
    items = discover(course, course.fetch(course.BASE))
    failures = []
    for url, kind in sorted(items.items()):
        print('Checking ' + url, flush=True)
        try:
            records[url] = update_item(course, url, kind, records.get(url, {}))
        except Exception as error:
            failures.append(dict(url=url, error=str(error)))
            print('FAILED: ' + str(error), file=sys.stderr, flush=True)
    payload = dict(source=course.BASE, retrieved_at=datetime.now(timezone.utc).isoformat(),
                   scope='Published Fall 2026 Labs, Homework and assigned Reading. Existing exercises are preserved.',
                   records=list(records.values()), failures=failures)
    course.replace_generated(manifest_path, (json.dumps(payload, ensure_ascii=False, indent=2)+'\n').encode())
    lines = ['# CS 61A · Fall 2026', '', '更新时间：' + payload['retrieved_at'], '',
             '仅同步本学期官网已发布的 Lab、HW 和 Reading，不混入其他学期。', '',
             '运行 `cs update` 检查更新。已有练习代码不会被覆盖；官网不同版本存于 `private/upstream/`。',
             '答案保存在忽略目录 `private/answers/fa26/`；旧 PDF 和索引备份于 `private/update-backups/`。',
             'PDF 为静态阅读版，交互内容和动画请访问官网。', '',
             '| 类型 | 资料 | 来源 |', '| --- | --- | --- |']
    for r in records.values():
        relative = (course.ROOT / r['pdf']).relative_to(course.DEST).as_posix()
        lines.append(f"| {r['kind']} | [{r['title']}]({relative}) | [官网]({r['url']}) |")
    if failures:
        lines += ['', '本次部分更新失败，详见 manifest.json 的 failures；保留此前资料。']
    course.replace_generated(course.DEST / 'README.md', ('\n'.join(lines)+'\n').encode())
    kept = sum(len(r.get('preserved_local_files', [])) for r in records.values())
    print(f'Complete: {len(items)-len(failures)}/{len(items)} resources checked; {kept} local files preserved; {len(failures)} failures.')
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Update official CS61A course materials safely.')
    parser.add_argument('command', choices=['update'])
    parser.parse_args(argv)
    try:
        import download_course as course
    except ImportError as error:
        print('Missing PDF dependency: ' + str(error), file=sys.stderr)
        return 1
    # OS file locking releases automatically even if a previous update was interrupted.
    lock_path = course.ROOT / 'private/cs-update.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a+b') as lock:
        import msvcrt
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print('Another cs update is running.', file=sys.stderr)
            return 1
        try:
            return update(course)
        except Exception as error:
            print('Update failed: ' + str(error), file=sys.stderr)
            return 1
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == '__main__':
    raise SystemExit(main())
