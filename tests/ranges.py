# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full's dependencies, in the RPM spec and debian/control alike: every one a floor only, no ceiling (owner
# rule 2026-11-16, superseding ruling R-107); the same floors in both; plugin-hostd a range like the others, never pinned to this package's own version (ruling
# 2026-11-09: plugin-hostd-full is its own repository, released last in each wave).
#
# Usage: ranges.py [root]. It first proves it sees each kind of broken range on a planted copy of the files.
import os, re, sys, tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SPEC, CONTROL = "packaging/plugin-hostd-full.spec", "debian/control"
WANT = {"plugin-hostd", "omx-clap-host", "omx-plugins", "plugin-qualify", "omx-panel", "plugin-qualification-records"}


def read(root, path):
    with open(os.path.join(root, path)) as f:
        return f.read()


def spec_ranges(text):
    out, bad = {}, []
    for kind, dep in re.findall(r"^(Requires|Recommends):\s*(.+)$", text, re.M):
        m = re.fullmatch(r"(\S+) >= (\S+)", dep.strip())
        if not m:
            bad.append(f"spec: {kind}: {dep.strip()} is not <name> >= <floor> (a floor only, no ceiling)")
            continue
        out[m.group(1)] = (kind, m.group(2))
    return out, bad


def control_ranges(text):
    stanza = text[text.index("Package: plugin-hostd-full"):].split("\n\n")[0]
    out, bad = {}, []
    for field, kind in (("Depends", "Requires"), ("Recommends", "Recommends")):
        m = re.search(rf"^{field}:((?:.*\n)(?:[ \t].*\n)*)", stanza + "\n", re.M)
        if not m:
            continue
        items = [i.strip() for i in m.group(1).replace("\n", " ").split(",") if i.strip() and not i.strip().startswith("${")]
        seen = {}
        for i in items:
            mm = re.fullmatch(r"(\S+) \(>= (\S+?)~\)", i)
            if not mm:
                bad.append(f"debian/control: {field}: {i} is not <name> (>= <floor>~) (a floor only, no ceiling)")
                continue
            if mm.group(1) in seen:
                bad.append(f"debian/control: {mm.group(1)} is named twice in {field}")
            seen[mm.group(1)] = (kind, mm.group(2))
        out.update(seen)
    return out, bad


def problems(root):
    spec, sb = spec_ranges(read(root, SPEC))
    control, cb = control_ranges(read(root, CONTROL))
    p = sb + cb
    if re.search(r"plugin-hostd\s*=", read(root, SPEC)) or re.search(r"plugin-hostd \(= ", read(root, CONTROL)):
        p.append("plugin-hostd is pinned to one version: it is a range like every other dependency")
    for where, ranges in (("spec", spec), ("debian/control", control)):
        if set(ranges) != WANT:
            p.append(f"{where}: depends on {sorted(ranges)}, not {sorted(WANT)}")
    for name in sorted(set(spec) & set(control)):
        if spec[name] != control[name]:
            p.append(f"{name}: {spec[name]} in the spec, {control[name]} in debian/control")
    return p


def planted():
    """each kind of broken range planted in a copy: every one must be seen"""
    spec, control = read(ROOT, SPEC), read(ROOT, CONTROL)
    cases = {
        "a ceiling (spec)": (SPEC, spec.replace("Requires: omx-plugins >= 0.19.5", "Requires: (omx-plugins >= 0.19.5 with omx-plugins < 0.20)")),
        "a ceiling (deb)": (CONTROL, control.replace("omx-plugins (>= 0.19.5~),", "omx-plugins (>= 0.19.5~), omx-plugins (<< 0.20~),")),
        "plugin-hostd pinned": (SPEC, spec.replace("Requires: plugin-hostd >= 0.20.8",
                                                    "Requires: plugin-hostd = %{version}-%{release}")),
        "the spec and the deb apart": (CONTROL, control.replace("plugin-qualify (>= 0.20.6~)", "plugin-qualify (>= 0.20.7~)")),
        "a dependency dropped": (CONTROL, control.replace("            plugin-qualification-records (>= 2026110902~)\n", "").replace("omx-panel (>= 0.13.9~),", "omx-panel (>= 0.13.9~)")),
    }
    missed = []
    for kind, (path, text) in cases.items():
        if text == read(ROOT, path):
            missed.append(kind + " (nothing planted)")
            continue
        with tempfile.TemporaryDirectory() as t:
            for f in (SPEC, CONTROL):
                os.makedirs(os.path.join(t, os.path.dirname(f)), exist_ok=True)
                with open(os.path.join(t, f), "w") as w:
                    w.write(text if f == path else read(ROOT, f))
            if not problems(t):
                missed.append(kind)
    return missed


missed = planted()
if missed:
    print("ranges: the check does not see " + "; ".join(missed))
    sys.exit(2)
p = problems(ROOT)
for line in p:
    print("FAIL " + line)
if p:
    sys.exit(1)
print("ok   plugin-hostd-full: every dependency a floor only, no ceiling, the same in the spec and debian/control")
