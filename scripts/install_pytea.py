"""Install a tiny launcher without downloading packages or changing PATH."""
import os
from pathlib import Path
import sys
import sysconfig


def main():
    root = Path(__file__).resolve().parents[1]
    if os.name == 'nt':
        destination = Path(sysconfig.get_path('scripts')) / 'pytea.cmd'
        content = f'@echo off\r\nrem pytea managed launcher\r\npushd "{root}"\r\n"{sys.executable}" -m pytea %*\r\npopd\r\n'
    else:
        import shlex
        destination = Path.home() / '.local' / 'bin' / 'pytea'
        content = f'#!/bin/sh\n# pytea managed launcher\ncd {shlex.quote(str(root))} || exit 1\nexec {shlex.quote(sys.executable)} -m pytea "$@"\n'
    if destination.exists() and 'pytea managed launcher' not in destination.read_text():
        raise SystemExit(f'Refusing to overwrite an existing command: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding='utf-8', newline='')
    if os.name != 'nt':
        destination.chmod(0o755)
    print(f'Installed: {destination}')
    print('Run: pytea')
    if str(destination.parent).casefold() not in [p.casefold() for p in os.environ.get('PATH', '').split(os.pathsep)]:
        print(f'Add this directory to PATH: {destination.parent}')


if __name__ == '__main__':
    main()
