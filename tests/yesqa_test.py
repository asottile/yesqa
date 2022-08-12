from __future__ import annotations

import pytest

import yesqa


@pytest.fixture
def assert_rewrite(tmpdir):
    def _assert(s, expected=None):
        expected_retc = 0 if expected is None else 1
        expected = s if expected is None else expected
        f = tmpdir.join('f.py')
        f.write(s)
        assert yesqa.fix_file(str(f)) == expected_retc
        assert f.read() == expected
    return _assert


def test_non_utf8_bytes(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary('x = "€"'.encode('cp1252'))
    assert yesqa.fix_file(str(f)) == 1
    out, _ = capsys.readouterr()
    assert out == f'{f} is non-utf8 (not supported)\n'


@pytest.mark.parametrize(
    'src',
    (
        '',  # noop
        '# hello\n',  # comment at beginning of file
        # still needed
        'import os  # noqa\n',
        'import os  # NOQA\n',
        'import os  # noqa: F401\n',
        'import os  # noqa:F401\n',
        'import os  # noqa: F401 isort:skip\n',
        'import os  # isort:skip # noqa\n',
        'import os  # isort:skip # noqa: F401\n',
        '"""\n' + 'a' * 40 + ' ' + 'b' * 60 + '\n""" # noqa\n',
        'from foo\\\nimport bar  # noqa\n',
        # don't rewrite syntax errors
        'import x  # noqa\nx() = 5\n',

        'A' * 65 + ' = int\n\n\n'
        'def f():\n'
        '    # type: () -> ' + 'A' * 65 + '  # noqa\n'
        '    pass\n',
        'def foo(w: Sequence[int], x: Sequence[int], y: int, z: int) -> bar: ...  # noqa: E501, F821\n',
        'def foo(w: Sequence[int]) -> bar:  # foobarfoobarfoobarfoobarfoobarfoo   # noqa: E501, F821\n',
    ),
)
def test_ok(assert_rewrite, src):
    assert_rewrite(src)


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        # line comments
        ('x = 1  # noqa\n', 'x = 1\n'),
        ('import os  # noqa: F401,X999\n', 'import os  # noqa: F401\n'),
        ('import os  # noqa:F401,X999\n', 'import os  # noqa: F401\n'),
        ('# foo # noqa\nx = 1\n', '# foo\nx = 1\n'),
        ('# noqa # foo\nx = 1\n', '# foo\nx = 1\n'),
        (
            'try:\n'
            '    pass\n'
            'except OSError:  # noqa hi\n'
            '    pass\n',
            'try:\n'
            '    pass\n'
            'except OSError:  # hi\n'
            '    pass\n',
        ),
        (
            'import os  # noqa\n'
            '# hello world\n'
            'os\n',
            'import os\n'
            '# hello world\n'
            'os\n',
        ),
        (
            '# a  # noqa: E501\n',
            '# a\n',
        ),
        pytest.param(
            'if x==1:  # noqa: F401\n'
            '    pass\n',
            'if x==1:\n'
            '    pass\n',
            id='wrong noqa',
        ),
        pytest.param(
            'x = 1  # foo # noqa: ABC123\n',
            'x = 1  # foo\n',
            id='multi-character noqa code',
        ),
        # file comments
        ('# flake8: noqa\nx = 1\n', 'x = 1\n'),
        ('x = 1  # flake8: noqa\n', 'x = 1\n'),
    ),
)
def test_rewrite(assert_rewrite, src, expected):
    assert_rewrite(src, expected)


def test_main(tmpdir, capsys):
    f = tmpdir.join('f.py').ensure()
    g = tmpdir.join('g.py')
    g.write('x = 1  # noqa\n')
    ret = yesqa.main((str(f), str(g)))
    assert ret == 1
    assert g.read() == 'x = 1\n'
    out, _ = capsys.readouterr()
    assert out == f'Rewriting {g}\n'


def test_show_source_in_config(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write('import os  # noqa\n')
    tmpdir.join('tox.ini').write('[flake8]\nshow_source = true\n')
    with tmpdir.as_cwd():
        ret = yesqa.main((str(f),))
    assert ret == 0
    assert f.read() == 'import os  # noqa\n'


def test_flake8_fails_to_run(assert_rewrite, monkeypatch):
    cmd = (
        'python',
        '-c',
        'import sys; sys.exit(1)',
    )
    monkeypatch.setattr('yesqa.CMD', cmd)
    src = 'foo  # noqa: E501'
    assert_rewrite(src)
