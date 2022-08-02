from __future__ import annotations

import argparse
import collections
import os.path
import re
import subprocess
import sys
import tempfile
from typing import List
from typing import Match
from typing import Sequence

import tokenize_rt

Tokens = List[tokenize_rt.Token]

NOQA_FILE_RE = re.compile(r'^# flake8[:=]\s*noqa', re.I)
_code = '[a-z]{1,3}[0-9]+'
_sep = r'[,\s]+'
NOQA_RE = re.compile(f'# noqa(: ?{_code}({_sep}{_code})*)?', re.I)
SEP_RE = re.compile(_sep)


def _run_flake8(filename: str) -> dict[int, set[str]]:
    cmd = (
        sys.executable,
        '-mflake8',
        '--format=%(row)d\t%(code)s',
        '--no-show-source',
        filename,
    )
    out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    ret: dict[int, set[str]] = collections.defaultdict(set)
    for line in out.decode().splitlines():
        lineno, code = line.split('\t')
        ret[int(lineno)].add(code)
    return ret


def _remove_comment(tokens: Tokens, i: int) -> None:
    if i > 0 and tokens[i - 1].name == tokenize_rt.UNIMPORTANT_WS:
        del tokens[i - 1:i + 1]
    else:
        del tokens[i]


def _remove_comments(tokens: Tokens) -> Tokens:
    tokens = list(tokens)
    for i, token in tokenize_rt.reversed_enumerate(tokens):
        if token.name == 'COMMENT':
            if NOQA_RE.search(token.src):
                _mask_noqa_comment(tokens, i)
            elif NOQA_FILE_RE.search(token.src):
                _remove_comment(tokens, i)
    return tokens


def _mask_noqa_comment(tokens: Tokens, i: int) -> None:
    token = tokens[i]
    match = NOQA_RE.search(token.src)
    assert match is not None

    def _sub(match: Match[str]) -> str:
        return f'# {"."*(len(match.group())-2)}'

    src = NOQA_RE.sub(_sub, token.src)
    tokens[i] = token._replace(src=src)


def _rewrite_noqa_comment(
        tokens: Tokens,
        i: int,
        flake8_results: dict[int, set[str]],
) -> None:
    # find logical lines that this noqa comment may affect
    lines: set[int] = set()
    j = i
    while j >= 0 and tokens[j].name not in {'NL', 'NEWLINE'}:
        t = tokens[j]
        if t.line is not None:  # pragma: no branch (tokenize-rt<4.2.1)
            lines.update(range(t.line, t.line + t.src.count('\n') + 1))
        j -= 1

    lints = set()
    for line in lines:
        lints.update(flake8_results[line])

    token = tokens[i]
    match = NOQA_RE.search(token.src)
    assert match is not None

    def _remove_noqa() -> None:
        assert match is not None
        if match.group() == token.src:
            _remove_comment(tokens, i)
        else:
            src = NOQA_RE.sub('', token.src).strip()
            if not src.startswith('#'):
                src = f'# {src}'
            tokens[i] = token._replace(src=src)

    # exclude all lints on the line but no lints
    if not lints:
        _remove_noqa()
    elif match.group().lower() != '# noqa':
        codes = set(SEP_RE.split(match.group(1)[1:]))
        expected_codes = codes & lints
        if not expected_codes:
            _remove_noqa()
        elif expected_codes != codes:
            comment = f'# noqa: {", ".join(sorted(expected_codes))}'
            tokens[i] = token._replace(src=NOQA_RE.sub(comment, token.src))


def fix_file(filename: str) -> int:
    with open(filename, 'rb') as f:
        contents_bytes = f.read()

    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f'{filename} is non-utf8 (not supported)')
        return 1

    tokens = tokenize_rt.src_to_tokens(contents_text)

    tokens_no_comments = _remove_comments(tokens)
    src_no_comments = tokenize_rt.tokens_to_src(tokens_no_comments)

    if src_no_comments == contents_text:
        return 0

    fd, path = tempfile.mkstemp(
        dir=os.path.dirname(filename),
        prefix=os.path.basename(filename),
        suffix='.py',
    )
    try:
        with open(fd, 'wb') as f:
            f.write(src_no_comments.encode())
        flake8_results = _run_flake8(path)
    finally:
        os.remove(path)

    if any('E999' in v for v in flake8_results.values()):
        print(f'{filename}: syntax error (skipping)')
        return 0

    for i, token in tokenize_rt.reversed_enumerate(tokens):
        if token.name != 'COMMENT':
            continue

        if NOQA_RE.search(token.src):
            _rewrite_noqa_comment(tokens, i, flake8_results)
        elif NOQA_FILE_RE.match(token.src) and not flake8_results:
            if i == 0 or tokens[i - 1].name == 'NEWLINE':
                del tokens[i: i + 2]
            else:
                _remove_comment(tokens, i)

    newsrc = tokenize_rt.tokens_to_src(tokens)
    if newsrc != contents_text:
        print(f'Rewriting {filename}')
        with open(filename, 'wb') as f:
            f.write(newsrc.encode())
        return 1
    else:
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= fix_file(filename)
    return retv


if __name__ == '__main__':
    raise SystemExit(main())
