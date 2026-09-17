"""Trace subprocess; a file keeps user stdout separate from the protocol."""
import json
import sys
from pathlib import Path
from .tracer import trace_code


def main():
    request = json.loads(sys.stdin.read())
    result = trace_code(request['code'], request.get('inputs', ''))
    Path(sys.argv[1]).write_text(json.dumps(result, ensure_ascii=True), encoding='utf-8')


if __name__ == '__main__':
    main()
