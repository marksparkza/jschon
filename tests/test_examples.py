import io
import pathlib
from contextlib import redirect_stdout
from importlib import import_module

examples_dir = pathlib.Path(__file__).parent.parent / 'examples'


def pytest_generate_tests(metafunc):
    argnames = ('module_name', 'module_output')
    argvalues = []
    testids = []
    pyfiles = sorted(examples_dir.glob('*.py'))
    for pyfile in pyfiles:
        name = pyfile.stem
        outfile = examples_dir / 'output' / f'{name}.txt'
        with open(outfile) as f:
            output = f.read()
        argvalues.append((f'examples.{name}', output))
        testids.append(name)

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_example(module_name, module_output):
    with redirect_stdout(io.StringIO()) as o:
        import_module(module_name)
    assert o.getvalue() == module_output
