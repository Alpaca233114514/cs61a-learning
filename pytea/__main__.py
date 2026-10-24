import argparse
import hmac
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent


def execute(payload):
    with tempfile.TemporaryDirectory(prefix='pytea-') as folder:
        target = Path(folder) / 'trace.json'
        try:
            proc = subprocess.run([sys.executable, '-m', 'pytea.worker', str(target)],
                                  input=json.dumps(payload), text=True, encoding='utf-8',
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  cwd=ROOT.parent, timeout=5,
                                  creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except subprocess.TimeoutExpired:
            return {'error': '运行超过 5 秒，已停止执行。请检查循环或缩小示例。'}
        if proc.returncode or not target.exists():
            return {'error': '执行进程提前退出，无法生成轨迹。'}
        if target.stat().st_size > 30_000_000:
            return {'error': '轨迹过大，请缩小示例。'}
        return json.loads(target.read_text(encoding='utf-8'))


def make_handler(token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, body, content_type='application/json; charset=utf-8'):
            data = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, '{}')
            routes = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                      '/style.css': ('style.css', 'text/css')}
            path = self.path.split('?')[0]
            if path not in routes:
                return self.send(404, '{}')
            filename, mime = routes[path]
            self.send(200, (ROOT / 'static' / filename).read_text(encoding='utf-8'), mime + '; charset=utf-8')

        def do_POST(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if (not self.valid_host() or self.headers.get('Origin') != origin or
                    not hmac.compare_digest(self.headers.get('X-Pytea-Token', ''), token)):
                return self.send(403, '{}')
            if self.path != '/trace':
                return self.send(404, '{}')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 64000:
                    return self.send(413, '{}')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload.get('code'), str) or not isinstance(payload.get('inputs', ''), str):
                    raise ValueError('invalid request')
            except (ValueError, AttributeError):
                return self.send(400, '{}')
            if not self.server.run_lock.acquire(blocking=False):
                return self.send(429, json.dumps({'error': '程序正在运行，请稍后再试。'}))
            try:
                result = execute(payload)
                self.send(200, json.dumps(result, ensure_ascii=True))
            finally:
                self.server.run_lock.release()
    return Handler


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Pytea · 本地 Python 导师')
    parser.add_argument('--port', type=int, default=0, help='本地端口，默认自动分配')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    args = parser.parse_args()
    token = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(token))
    server.daemon_threads = True
    server.run_lock = threading.Lock()
    url = f'http://127.0.0.1:{server.server_port}/#token={token}'
    print('Pytea · 本地 Python 导师\n仅运行你信任的代码。按 Ctrl+C 退出。\n' + url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nPytea 已关闭。')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
