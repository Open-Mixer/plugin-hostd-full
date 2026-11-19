#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# Fedora 44 is dropped from this pass (protocol 0.6.0 and later are published for fc45 only): no workflow may target
# fedora:44, fc44 or a Fedora 44 matrix cell. Refuses any such reference under .github/workflows of the tree given.
#   no_fedora44_cells.sh <tree>       0 when no workflow names Fedora 44; else each line naming it, and 1
#   no_fedora44_cells.sh --self-test  a planted fedora:44 and a planted fedora: [44, 45] must each be refused; a clean one passes
set -euo pipefail
pat='(fedora|fc)[: ]*\[?[ ,]*44\b|fc44'
if [ "${1:-}" = "--self-test" ]; then
	t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
	for fixture in 'image: fedora:44' 'fedora: [44, 45]' 'name: RPM (fc44)'; do
		mkdir -p "$t/.github/workflows"
		printf '%s\n' "$fixture" > "$t/.github/workflows/x.yml"
		if ! grep -qiE "$pat" "$t/.github/workflows/x.yml"; then echo "self-test: '$fixture' not refused"; exit 1; fi
	done
	printf '%s\n' 'image: fedora:45' 'fedora: [45]' > "$t/.github/workflows/x.yml"
	if grep -qiE "$pat" "$t/.github/workflows/x.yml"; then echo "self-test: clean fixture refused"; exit 1; fi
	echo "no_fedora44_cells self-test: ok"
	exit 0
fi
tree=${1:-.}
hits=$(grep -rniE "$pat" "$tree/.github/workflows" 2>/dev/null || true)
if [ -n "$hits" ]; then
	printf '%s\n' "$hits"
	echo "no_fedora44_cells: Fedora 44 is dropped for this pass; move these to fedora:45 / fc45"
	exit 1
fi
echo "no_fedora44_cells: ok"
