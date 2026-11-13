# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full: a metapackage, nothing to build. `make check` is what CI and the package builds run.
#   make check   every dependency a floor and a ceiling, the same in the spec and debian/control (tests/ranges.py),
#                and the kept-install check's own arguments (tools/full-install-check.sh --self-test)
.PHONY: all check
all:
check:
	python3 tests/ranges.py
	bash tools/full-install-check.sh --self-test
