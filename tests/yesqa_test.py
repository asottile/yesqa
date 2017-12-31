# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

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
    assert out == '{} is non-utf8 (not supported)\n'.format(f)


@pytest.mark.parametrize(
    'src',
    (
        '',  # noop
        '# hello\n',  # comment at beginning of file
        # still needed
        'import os  # noqa\n',
        'import os  # NOQA\n',
        'import os  # noqa: F401\n',
        '"""\n' + 'a' * 40 + ' ' + 'b' * 60 + '\n""" # noqa\n',
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
    assert out == 'Rewriting {}\n'.format(g)
