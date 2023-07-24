import json
import pathlib
import warnings

import pytest

from jschon import JSON, JSONSchema, LocalSource, URI
from jschon.utils import json_loadf
from tests import metaschema_uri_2019_09, metaschema_uri_2020_12, metaschema_uri_next

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'


class SuiteStatus:
    STATUS_PATH = pathlib.Path(__file__).parent / 'suite_status.json'
    _instance = None

    @classmethod
    def get_instance(cls, metafunc=None, generate_new=False):
        # "singleton" because this it just needs to be easily
        # available to both the metafunc and the module fixture.
        if not cls._instance:
            cls._instance = cls(metafunc, generate_new)
        return cls._instance

    def __init__(self, metafunc, generate_new):
        with open(self.STATUS_PATH) as status_fp:
            self._status = json.load(status_fp)
            self._generate_new = generate_new

    def get(self, version: str, path: str, case: str, test: str) -> dict:
        return self._status.get(version, {}).get(path, {}).get(case, {}).get(test, {})

    def update(self, version: str, path: str, case: str, test: str, outcome: bool) -> None:
        if not self._generate_new:
            return

        if outcome is True:
            self.delete(version, path, case, test)
            return

        status_obj = self._status \
            .setdefault(version, {}) \
            .setdefault(path, {}) \
            .setdefault(case, {}) \
            .setdefault(test, {})

        # Don't overwite existing statuses in case they were customized.
        if status_obj:
            return

        # We only xfail optional tests (including formats) and tests from draft-next.
        # The skip status can be added to the file manually for tests that have bugs
        # (in the test case/suite itself) making them impossible to run.
        fmt = 'format assertions not supported' if path.startswith('optional/format/') else None
        opt = 'unsupported optional test' if path.startswith('optional/') else None
        nxt = 'draft-next support in progress' if version == 'next' else None

        if any((fmt, opt, nxt)):
            status_obj['status'] = 'xfail'
            status_obj['reason'] = next(filter(None, (fmt, opt, nxt)))

    def delete(self, version: str, path: str, case: str, test: str) -> None:
        try:
            del self._status[version][path][case][test]
            del self._status[version][path][case]
            del self._status[version][path]
            del self._status[version]
        except KeyError:
            pass

    def write(self):
        if self._generate_new:
            with open(self.STATUS_PATH, mode='w') as status_fp:
                json.dump(self._status, status_fp, indent=2)


@pytest.fixture(autouse=True, scope='module')
def status_data():
    yield
    SuiteStatus.get_instance().write()


@pytest.fixture(autouse=True)
def setup_remotes(catalog):
    catalog.add_uri_source(
        URI.get('http://localhost:1234/'),
        LocalSource(testsuite_dir / 'remotes'),
    )


def pytest_generate_tests(metafunc):
    argnames = ('metaschema_uri', 'schema', 'data', 'valid', 'test_id')
    argvalues = []
    testids = []

    gen_status_data = metafunc.config.getoption("testsuite_generate_status")
    status_data = SuiteStatus.get_instance(metafunc, gen_status_data)
    if gen_status_data:
        test_versions = ('2019-09', '2020-12', 'next')
        include_optionals = True
        include_formats = True
        test_files = []
        test_descriptions = []
    else:
        test_versions = metafunc.config.getoption("testsuite_version")
        include_optionals = metafunc.config.getoption("testsuite_optionals")
        include_formats = metafunc.config.getoption("testsuite_formats")
        test_files = metafunc.config.getoption("testsuite_file")
        test_descriptions = metafunc.config.getoption("testsuite_description")

    if not test_versions:
        test_versions = ['2019-09', '2020-12']

    base_dir = testsuite_dir / 'tests'
    version_dirs = {
        '2019-09': (metaschema_uri_2019_09, base_dir / 'draft2019-09'),
        '2020-12': (metaschema_uri_2020_12, base_dir / 'draft2020-12'),
        'next': (metaschema_uri_next, base_dir / 'draft-next'),
    }

    for version, (metaschema_uri, dir_) in version_dirs.items():
        testfile_paths = []

        if not test_versions or version in test_versions:
            if test_files:
                for tf in test_files:
                    tf_path = dir_.joinpath(tf)
                    if tf_path.exists():
                        testfile_paths.append(tf_path)
                    else:
                        # Warn because it might exist under other versions
                        warnings.warn(f'Test suite file "{tf_path}" does not exist for "{version}"')

            else:
                testfile_paths += sorted(dir_.glob('*.json'))
                if include_optionals:
                    testfile_paths += sorted((dir_ / 'optional').glob('*.json'))
                if include_formats:
                    testfile_paths += sorted((dir_ / 'optional' / 'format').glob('*.json'))

        for testfile_path in testfile_paths:
            testcases = json_loadf(testfile_path)
            for testcase in testcases:
                for test in testcase['tests']:
                    if test_descriptions and not any(
                            s.lower() in testcase['description'].lower() or s.lower() in test['description'].lower()
                            for s in test_descriptions
                    ):
                        continue

                    relpath = testfile_path.relative_to(dir_)
                    case_desc = testcase['description'].strip()
                    test_desc = test['description'].strip()
                    test_id = (version, str(relpath), case_desc, test_desc)
                    status = status_data.get(*test_id)

                    params = [metaschema_uri, testcase['schema'], test['data'], test['valid'], test_id]
                    if status and not gen_status_data:
                        status_mark = {
                            'xfail': pytest.mark.xfail,
                            'skip': pytest.mark.skip,
                        }[status['status']].with_args(reason=status['reason'])
                        argvalues.append(pytest.param(*params, marks=status_mark))
                    else:
                        argvalues.append(pytest.param(*params))

                    testids.append(f"{version} -> {relpath} -> {case_desc} -> {test_desc}")

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_validate(metaschema_uri, schema, data, valid, test_id):
    try:
        outcome = True
        json_schema = JSONSchema(schema, metaschema_uri=metaschema_uri)
        json_data = JSON(data)
        result = json_schema.evaluate(json_data).valid
        assert result is valid
    except Exception:
        outcome = False
        raise
    finally:
        SuiteStatus.get_instance().update(*test_id, outcome)
