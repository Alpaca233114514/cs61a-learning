"""Bounded snapshots of real CPython execution (not a security sandbox)."""
import contextlib
import builtins
import io
import itertools
import sys
import types

FILENAME = '<pytea>'
MAX_STEPS = 600


class TraceLimit(BaseException):
    pass


class Output(io.StringIO):
    def write(self, value):
        if self.tell() + len(value) > 20000:
            raise TraceLimit('输出超过 20,000 字符，请缩小示例。')
        return super().write(value)


def trace_code(source, inputs=''):
    steps, stack, kept, ids = [], [], [], {}
    output = Output()
    previous = None
    pending_exceptions = {}
    answers = iter(inputs.splitlines())

    def read_input(prompt=''):
        print(prompt, end='')
        try:
            answer = next(answers)
        except StopIteration:
            raise EOFError('请在「输入数据」中为每次 input() 提供一行。') from None
        print(answer)
        return answer

    namespace = {'__name__': '__main__', '__builtins__': dict(vars(builtins), input=read_input)}

    def snapshot(event, line=None, result=None, error=None):
        objects = {}

        def encode(value, depth=0):
            if type(value) in (type(None), bool, int, float, str):
                try:
                    label = repr(value)
                except ValueError:
                    label = '<整数过大>'
                return {'text': label[:500]}
            identity = id(value)
            if identity not in ids:
                ids[identity] = 'o' + str(len(ids) + 1)
                kept.append(value)
            key = ids[identity]
            if key in objects:
                return {'ref': key}
            if len(objects) >= 100 or depth > 7:
                return {'text': '…（对象展开上限）'}
            obj = {'id': key, 'type': type(value).__name__, 'items': []}
            objects[key] = obj
            if isinstance(value, (types.FunctionType, types.BuiltinFunctionType)):
                obj['label'] = 'func ' + value.__name__ + '(…)'
                if isinstance(value, types.FunctionType):
                    obj['line'] = value.__code__.co_firstlineno
                    for name, cell in zip(value.__code__.co_freevars, value.__closure__ or ()):
                        try:
                            obj['items'].append([name, encode(cell.cell_contents, depth + 1)])
                        except ValueError:
                            pass
            elif type(value) in (list, tuple, set, frozenset):
                obj['items'] = [[str(i), encode(v, depth + 1)] for i, v in enumerate(itertools.islice(value, 50))]
                obj['size'] = len(value)
            elif type(value) is dict:
                obj['items'] = [[encode(k, depth + 1), encode(v, depth + 1)] for k, v in itertools.islice(value.items(), 50)]
                obj['size'] = len(value)
            elif isinstance(value, types.ModuleType):
                obj['label'] = 'module ' + value.__name__
            elif isinstance(value, type):
                obj['label'] = 'class ' + value.__name__
            else:
                # Do not invoke user __repr__ or properties while observing values.
                obj['label'] = type(value).__name__ + ' instance'
                try:
                    attrs = object.__getattribute__(value, '__dict__')
                except (AttributeError, TypeError):
                    attrs = {}
                if type(attrs) is dict:
                    obj['items'] = [[str(k), encode(v, depth + 1)] for k, v in list(attrs.items())[:50]]
            return {'ref': key}

        def bindings(values):
            return [[name, encode(value)] for name, value in list(values.items())[:150]
                    if not name.startswith('__')]

        frames = [{'name': 'Global frame', 'id': 'global', 'vars': bindings(namespace)}]
        for i, frame in enumerate(stack):
            if frame.f_code.co_name == '<module>':
                continue
            item = {'name': frame.f_code.co_name, 'id': 'f' + str(i), 'vars': bindings(frame.f_locals)}
            if event == 'return' and frame is stack[-1]:
                item['vars'].append(['↩ return', encode(result)])
            frames.append(item)
        steps.append({'event': event, 'line': line, 'previous': previous,
                      'frames': frames, 'objects': list(objects.values()),
                      'output': output.getvalue(), 'error': error})

    def observer(frame, event, arg):
        nonlocal previous
        if frame.f_code.co_filename != FILENAME:
            return None
        if len(steps) >= MAX_STEPS:
            raise TraceLimit('已达到 600 步上限，请缩小示例。')
        if event == 'call':
            stack.append(frame)
        elif event == 'line':
            pending_exceptions.pop(frame, None)
            snapshot('line', frame.f_lineno)
            previous = frame.f_lineno
        elif event == 'return':
            previous = frame.f_lineno
            if frame in pending_exceptions:
                snapshot('exception', error=pending_exceptions.pop(frame))
            else:
                snapshot('return', result=arg)
            if frame in stack:
                stack.remove(frame)
        elif event == 'exception':
            message = arg[0].__name__ + ': ' + str(arg[1])
            pending_exceptions[frame] = message
            snapshot('exception', frame.f_lineno, error=message)
        return observer

    try:
        code = compile(source, FILENAME, 'exec')
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            sys.settrace(observer)
            try:
                exec(code, namespace)
            finally:
                sys.settrace(None)
        snapshot('done')
    except BaseException as exc:
        sys.settrace(None)
        snapshot('error', getattr(exc, 'lineno', None), error=type(exc).__name__ + ': ' + str(exc))
    return {'steps': steps}
