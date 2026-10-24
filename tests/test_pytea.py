import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pytea.tracer import trace_code
from pytea.__main__ import execute, make_handler


class TraceTests(unittest.TestCase):
    def test_example_and_snapshot_timing(self):
        steps = trace_code('f = min\nf = max\ng, h = min, max\nmax = g\nprint(max(f(2, g(h(1, 5), 3)), 4))')['steps']
        self.assertEqual(steps[-1]['output'], '3\n')
        self.assertEqual(steps[1]['line'], 2)
        self.assertEqual(steps[1]['objects'][0]['label'], 'func min(…)')

    def test_alias_cycle_and_snapshot_copy(self):
        steps = trace_code('a = [1]\nb = a\na.append(a)')['steps']
        final = steps[-1]
        values = dict(final['frames'][0]['vars'])
        self.assertEqual(values['a'], values['b'])
        obj = final['objects'][0]
        self.assertEqual(obj['items'][1][1]['ref'], obj['id'])
        self.assertEqual(steps[1]['objects'][0]['size'], 1)

    def test_recursion_and_closure(self):
        steps = trace_code('def f(n):\n    return 1 if n == 0 else n * f(n-1)\nprint(f(4))')['steps']
        self.assertEqual(steps[-1]['output'], '24\n')
        self.assertGreater(max(len(s['frames']) for s in steps), 4)
        result = trace_code('def factory(n):\n    def f(x):\n        return n+x\n    return f\na=factory(3)\nprint(a(4))')['steps'][-1]
        self.assertEqual(result['output'], '7\n')
        self.assertTrue(any(o['items'] == [['n', {'text': '3'}]] for o in result['objects']))

    def test_errors_inputs_and_limits(self):
        self.assertEqual(trace_code('bad syntax')['steps'][-1]['event'], 'error')
        self.assertIn('ZeroDivisionError', trace_code('1/0')['steps'][-1]['error'])
        self.assertEqual(trace_code('print(input())', '中文')['steps'][-1]['output'], '中文\n中文\n')
        steps = trace_code('while True:\n    pass')['steps']
        self.assertIn('600', steps[-1]['error'])
        self.assertLessEqual(len(steps), 601)
        self.assertIn('20,000', trace_code('print("x" * 21000)')['steps'][-1]['error'])

    def test_subprocess(self):
        self.assertEqual(execute({'code': 'print("你好")'})['steps'][-1]['output'], '你好\n')
        self.assertIn('5 秒', execute({'code': 'import time\ntime.sleep(10)'})['error'])

    def test_shadow_input_and_exception_unwinding(self):
        final = trace_code('input = 42')['steps'][-1]
        self.assertEqual(dict(final['frames'][0]['vars'])['input']['text'], '42')
        steps = trace_code('def f():\n    return 1/0\nf()')['steps']
        self.assertFalse(any(name == '↩ return' for step in steps for frame in step['frames'] for name, _ in frame['vars']))
        caught = trace_code('try:\n    1/0\nexcept ZeroDivisionError:\n    print("caught")')['steps'][-1]
        self.assertEqual(caught['event'], 'done')
        self.assertEqual(caught['output'], 'caught\n')


class ServerTests(unittest.TestCase):
    def test_auth_and_static(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler('test-token'))
        server.run_lock = threading.Lock()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urllib.request.urlopen(base) as response:
                self.assertIn('Pytea', response.read().decode())
            data = json.dumps({'code': 'print(42)'}).encode()
            with self.assertRaises(urllib.error.HTTPError) as rejected:
                urllib.request.urlopen(urllib.request.Request(base+'/trace', data=data))
            self.assertEqual(rejected.exception.code, 403)
            request = urllib.request.Request(base+'/trace', data=data, headers={'Origin': base, 'X-Pytea-Token': 'test-token'})
            with urllib.request.urlopen(request) as response:
                self.assertEqual(json.load(response)['steps'][-1]['output'], '42\n')
            for headers in [{'Origin': 'https://example.com', 'X-Pytea-Token': 'test-token'}, {'Origin': base, 'X-Pytea-Token': 'wrong'}]:
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(urllib.request.Request(base+'/trace', data=data, headers=headers))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
