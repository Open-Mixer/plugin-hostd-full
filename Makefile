# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full: a metapackage, nothing to build. `make check` is what CI and the package builds run.
#   make check   no dependency with a typed version, the same packages in the spec and debian/control (tests/deps.py),
#                the kept-install check's own arguments (tools/full-install-check.sh --self-test), and the records
#                package found for this machine's architecture alone (tests/records_candidate.sh), and the release workflow's
#                same-pass list read through the shared action (tests/release_same_pass.py), and no workflow naming Fedora 44
#                (tests/no_fedora44_cells.sh: red until the cells move to fc45)
.PHONY: all check
all:
check:
	python3 tests/deps.py
	bash tools/full-install-check.sh --self-test
	bash tests/records_candidate.sh
	bash tests/no_fedora44_cells.sh --self-test
	bash tests/no_fedora44_cells.sh .
	python3 tests/release_same_pass.py --self-test
	python3 tests/release_same_pass.py .
