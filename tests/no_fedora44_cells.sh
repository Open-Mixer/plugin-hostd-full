#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# Fedora 44 is dropped from this pass (protocol 0.6.0 and later are published for fc45 only): no workflow may target
# Fedora 44. Refused under .github/workflows of the tree given: fedora:44, fc44, Fedora 44, and 44 anywhere in a
# fedora matrix list ([45, 44], [43, 44]) or a block list (fedora:, then - 44). A missing workflows directory is a
# failure, never a clean pass.
#   no_fedora44_cells.sh <tree>       0 when no workflow names Fedora 44; 1 and each line naming it when one does;
#                                     2 when the workflows directory is missing or unreadable
#   no_fedora44_cells.sh --self-test  runs the tree mode on planted trees: every form above must be refused, a clean
#                                     fc45-only tree must pass, and a tree with no workflows directory must fail
set -uo pipefail
P1='(fedora|fc)[: ]*\[?[ ,]*44\b'
P2='fedora:?[[:space:]]*\[[^]]*\b44\b'

scan() {
	local dir="$1/.github/workflows" hits rc blk
	if [ ! -d "$dir" ]; then
		echo "no_fedora44_cells: no workflows directory at $dir; refusing to call it clean" >&2
		return 2
	fi
	hits=$(grep -rniE -e "$P1" -e "$P2" "$dir" 2>&1); rc=$?
	if [ "$rc" -ge 2 ]; then
		printf '%s\n' "$hits" >&2
		echo "no_fedora44_cells: grep failed on $dir" >&2
		return 2
	fi
	blk=$(find "$dir" -type f \( -name '*.yml' -o -name '*.yaml' \) -exec awk '
		FNR == 1 { fl = 0 }
		/^[[:space:]]*fedora:[[:space:]]*$/ { fl = FNR; next }
		fl && FNR - fl <= 4 && /^[[:space:]]*-[[:space:]]*.?44.?[[:space:]]*$/ { print FILENAME ":" FNR ": " $0 }
	' {} + 2>&1)
	if [ -n "$hits" ] || [ -n "$blk" ]; then
		[ -n "$hits" ] && printf '%s\n' "$hits"
		[ -n "$blk" ] && printf '%s\n' "$blk"
		echo "no_fedora44_cells: Fedora 44 is dropped for this pass; move these to fedora:45 / fc45"
		return 1
	fi
	echo "no_fedora44_cells: ok"
	return 0
}

if [ "${1:-}" = "--self-test" ]; then
	t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
	fails=0
	plant() {  # plant <name> <content with \n escapes>
		rm -rf "$t/tree"; mkdir -p "$t/tree/.github/workflows"
		printf '%b\n' "$2" > "$t/tree/.github/workflows/$1.yml"
	}
	expect() {  # expect <want rc> <label> <content>
		plant x "$3"
		scan "$t/tree" >/dev/null 2>&1; local got=$?
		if [ "$got" -ne "$1" ]; then echo "self-test: $2 gave rc $got, want $1"; fails=1; fi
	}
	expect 1 "fedora:44 image"             'image: fedora:44'
	expect 1 "fedora: [44, 45] first"      'fedora: [44, 45]'
	expect 1 "fedora: [45, 44] not first"  'fedora: [45, 44]'
	expect 1 "fedora: [43, 44] not first"  'fedora: [43, 44]'
	expect 1 "fc44 name"                   'name: RPM (fc44)'
	expect 1 "block list, 44 second"       'matrix:\n  fedora:\n    - 45\n    - 44'
	expect 1 "block list, 44 first, quoted" 'matrix:\n  fedora:\n    - "44"\n    - 45'
	expect 0 "clean fc45-only tree"        'image: fedora:45\nmatrix:\n  fedora: [45]\n  arch: [x86_64]'
	expect 0 "clean block list fc45"       'matrix:\n  fedora:\n    - 45'
	plant x 'image: fedora:45'; rm -rf "$t/tree/.github"
	scan "$t/tree" >/dev/null 2>&1; got=$?
	if [ "$got" -ne 2 ]; then echo "self-test: missing workflows dir gave rc $got, want 2"; fails=1; fi
	if [ "$fails" -ne 0 ]; then echo "no_fedora44_cells self-test: FAILED"; exit 1; fi
	echo "no_fedora44_cells self-test: ok"
	exit 0
fi
scan "${1:-.}"
