# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# release.yml reads the same-pass list exactly as plugin-hostd does: a same_pass input (dispatch and call), else the
# tracked .github/release-same-pass at the commit the run builds, read by a samepass job that the RPM and the DEB both
# need, and passed to each shared build as same-pass. The check first proves it sees each way the wiring can be cut
# on a planted copy of the workflow.
#
# Usage: same_pass_wiring.py [root]
import os, re, sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW = ".github/workflows/release.yml"
PASS = "${{ inputs.same_pass || needs.samepass.outputs.list }}"


def problems(text):
    bad = []
    if len(re.findall(r"^      same_pass:$", text, re.M)) != 2:
        bad.append("same_pass input is not declared under both workflow_dispatch and workflow_call")
    if ".github/release-same-pass" not in text:
        bad.append("nothing reads .github/release-same-pass")
    if not re.search(r"^  samepass:$", text, re.M):
        bad.append("no samepass job reads the list")
    if len(re.findall(r"^    needs: samepass$", text, re.M)) != 2:
        bad.append("the RPM and the DEB do not both need samepass")
    if text.count("same-pass: " + PASS) != 2:
        bad.append("the RPM and the DEB do not both pass the same-pass list to the shared build")
    return bad


def read(root):
    with open(os.path.join(root, WORKFLOW)) as f:
        return f.read()


def main():
    fail = 0
    real = read(ROOT)
    planted = {
        "dispatch input cut": re.sub(r"^      same_pass:$", "      other:", real, count=1, flags=re.M),
        "file read dropped": real.replace(".github/release-same-pass", ".github/none"),
        "rpm passes no list": real.replace("same-pass: " + PASS, "same-pass: ''", 1),
        "deb not ordered after samepass": real.replace("    needs: samepass\n", "", 2),
    }
    for label, text in planted.items():
        if not problems(text):
            print(f"FAIL self-test: planted '{label}' is not seen"); fail = 1
        else:
            print(f"ok   self-test sees: {label}")
    for p in problems(real):
        print(f"FAIL {WORKFLOW}: {p}"); fail = 1
    if not fail:
        print(f"ok   {WORKFLOW} reads the same-pass list as plugin-hostd does")
    return fail


if __name__ == "__main__":
    sys.exit(main())
