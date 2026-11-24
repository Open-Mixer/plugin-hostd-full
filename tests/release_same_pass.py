#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The packages other repositories release later in the same pass reach the channel-installability gate through this
# repository's release workflow by the SHARED action, never a copy: a samepass job calls
# Open-Mixer/.github/.github/actions/same-pass@openmixer-v1 (the dispatch same_pass input wins, else
# .github/release-same-pass at the commit built), and every shared build call (rpm, deb) needs that job and passes its
# list. This holds release.yml to that wiring:
#   a samepass job uses the shared action with list = inputs.same_pass and a ref of the built commit,
#   rpm and deb need samepass and pass same-pass: needs.samepass.outputs.list,
#   no other same-pass line in the workflow reads anything else.
#
#   release_same_pass.py <tree>       0 when the tree's release workflow is wired
#   release_same_pass.py --self-test  every way of unwiring, planted in a fixture, must be found; the wired fixture passes
import os
import sys
import tempfile

FILE = ".github/release-same-pass"
WIRED = "same-pass: ${{ needs.samepass.outputs.list }}"
ACTION = "Open-Mixer/.github/.github/actions/same-pass@openmixer-v1"
SOURCE_REF = "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.source-ref || github.sha }}"
SHARED = ("rpm", "deb")


def job_blocks(text):
    blocks, name, in_jobs = {}, None, False
    for line in text.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if line[:1] not in ("", " ", "#"):
            in_jobs = False
            continue
        if line.startswith("  ") and not line.startswith("   ") and line.strip().endswith(":") and not line.strip().startswith("#"):
            name = line.strip()[:-1]
            blocks[name] = []
            continue
        if name is not None:
            blocks[name].append(line)
    return {k: "\n".join(v) for k, v in blocks.items()}


def problems(text):
    found = []
    blocks = job_blocks(text)
    same = blocks.get("samepass", "")
    if ACTION not in same:
        found.append("no samepass job uses the shared action " + ACTION)
    if "list: ${{ inputs.same_pass }}" not in same:
        found.append("the samepass job does not pass the dispatch input as list")
    if "ref:" not in same:
        found.append("the samepass job passes no ref: the commit built")
    elif "source-ref:" in text and SOURCE_REF not in same:
        found.append("the workflow builds a source-ref but samepass does not read the list at it: ref must be " + SOURCE_REF)
    if "run:" in same:
        found.append("the samepass job reads the file itself: a copy of the shared reader")
    for job in SHARED:
        body = blocks.get(job)
        if body is None:
            found.append("no " + job + " job")
            continue
        if "needs: samepass" not in body and "needs: [samepass]" not in body:
            found.append(job + " does not need samepass")
        if "same-pass:" not in body:
            found.append(job + " passes no same-pass")
    for name, body in blocks.items():
        for line in body.splitlines():
            value = line.strip()
            if value.startswith("same-pass:") and value != WIRED:
                found.append(name + ": '" + value + "' is not the list read from " + FILE)
    return found


def fixture(wired=True, reads=True, needs=True, copied=False, source_ref=True, ref_sha=False):
    lines = [
        "name: release",
        "on:",
        "  workflow_dispatch:",
        "    inputs:",
        "      same_pass:",
        "        type: string",
        "        default: ''",
    ]
    if source_ref:
        lines += ["      source-ref:", "        type: string", "        default: ''"]
    lines += ["jobs:"]
    if reads:
        lines += [
            "  samepass:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - id: same",
        ]
        if copied:
            lines += ["        run: |", "          names=$(cat " + FILE + ")"]
        else:
            lines += [
                "        uses: " + ACTION,
                "        with:",
                "          list: ${{ inputs.same_pass }}",
                "          " + ("ref: ${{ github.sha }}" if ref_sha else SOURCE_REF),
            ]
    for job, uses in (("rpm", "build-rpm.yml"), ("deb", "build-deb.yml")):
        lines.append("  " + job + ":")
        if needs and reads:
            lines.append("    needs: samepass")
        lines += [
            "    uses: Open-Mixer/.github/.github/workflows/" + uses + "@openmixer-v1",
            "    with:",
            "      " + (WIRED if wired else "same-pass: ${{ inputs.same_pass || '' }}"),
            "    secrets: inherit",
        ]
    return "\n".join(lines) + "\n"


def self_test():
    cases = [
        ("the wired workflow passes", fixture(), False),
        ("the input-only wiring fails", fixture(wired=False), True),
        ("no samepass job fails", fixture(reads=False), True),
        ("a samepass job that copies the reader fails", fixture(copied=True), True),
        ("a source-ref input with ref: github.sha fails", fixture(ref_sha=True), True),
        ("no source-ref input with ref: github.sha passes", fixture(source_ref=False, ref_sha=True), False),
        ("rpm and deb that do not need samepass fail", fixture(needs=False), True),
    ]
    failed = []
    for label, text, want_red in cases:
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".github", "workflows"))
            with open(os.path.join(d, ".github", "workflows", "release.yml"), "w", encoding="utf-8") as f:
                f.write(text)
            red = bool(problems(text))
        if red != want_red:
            failed.append(label)
    for label in failed:
        print("FAIL release same-pass self-test: " + label)
    if failed:
        return 1
    print("ok   release same-pass self-test: %d planted workflows, every one found" % len(cases))
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return self_test()
    if len(argv) != 2:
        print("usage: release_same_pass.py <tree> | --self-test", file=sys.stderr)
        return 2
    path = os.path.join(argv[1], ".github", "workflows", "release.yml")
    with open(path, encoding="utf-8") as f:
        found = problems(f.read())
    for p in found:
        print("FAIL release same-pass: " + p)
    if found:
        return 1
    print("ok   release same-pass: release.yml reads the same-pass list through the shared action and passes it to rpm and deb")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
