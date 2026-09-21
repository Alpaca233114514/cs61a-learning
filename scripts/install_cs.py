"""Install cs.cmd in the current Python Scripts directory, without changing PATH."""
import argparse
import os
from pathlib import Path
import sysconfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', required=True, help='Python with lxml, reportlab and pypdf')
    args = parser.parse_args()
    interpreter = Path(args.python).resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    destination = Path(sysconfig.get_path('scripts')) / 'cs.cmd'
    if str(destination.parent).casefold() not in [p.rstrip('\\').casefold() for p in os.environ['PATH'].split(os.pathsep)]:
        raise SystemExit('Python Scripts is not on PATH; no changes made.')
    content = f'@echo off\r\nrem cs61a managed launcher\r\n"{interpreter}" "{root / "scripts/cs.py"}" %*\r\nexit /b %errorlevel%\r\n'
    if destination.exists():
        if destination.read_text(encoding='utf8').replace('\r\n','\n') != content.replace('\r\n','\n'):
            raise SystemExit(f'Refusing to replace existing command: {destination}')
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding='utf8', newline='')
    print(f'Installed: {destination}\nRun: cs update')


if __name__ == '__main__':
    main()
