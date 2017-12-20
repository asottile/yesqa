[![Build Status](https://travis-ci.org/asottile/yesqa.svg?branch=master)](https://travis-ci.org/asottile/yesqa)
[![Coverage Status](https://coveralls.io/repos/github/asottile/yesqa/badge.svg?branch=master)](https://coveralls.io/github/asottile/yesqa?branch=master)

yesqa
=====

A tool (and pre-commit hook) to automatically remove unnecessary `# noqa`
comments.

## Installation

`pip install yesqa`


## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/asottile/yesqa
    sha: v0.0.1
    hooks:
    -   id: yesqa
```

If you need to select a specific version of flake8 and/or run with specific
flake8 plugins, add them to [`additional_dependencies`][0].

[0]: http://pre-commit.com/#pre-commit-configyaml---hooks
