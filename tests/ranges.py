# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full's dependencies, in the RPM spec and debian/control alike: every one a floor and a ceiling (ruling
# R-107), the ceiling the next minor of the floor (the next year's first for the records' dated YYYYMMDDXX version); the
# same pairs in both; plugin-hostd a range like the others, never pinned to this package's own version (ruling
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
        m = re.fullmatch(r"\((\S+) >= (\S+) with \1 < (\S+)\)", dep.strip())
        if not m:
            bad.append(f"spec: {kind}: {dep.strip()} is not (<name> >= <floor> with <name> < <ceiling>)")
            continue
        out[m.group(1)] = (kind, m.group(2), m.group(3))
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
            mm = re.fullmatch(r"(\S+) \((>=|<<) (\S+?)~\)", i)
            if not mm:
                bad.append(f"debian/control: {field}: {i} is not <name> (>= <floor>~) or <name> (<< <ceiling>~)")
                continue
            seen.setdefault(mm.group(1), {})[mm.group(2)] = mm.group(3)
        for name, ops in seen.items():
            if set(ops) != {">=", "<<"}:
                bad.append(f"debian/control: {name} has no {'floor' if '>=' not in ops else 'ceiling'}")
                continue
            out[name] = (kind, ops[">="], ops["<<"])
    return out, bad


def next_ceiling(name, floor):
    if name == "plugin-qualification-records":
        return f"{int(floor[:4]) + 1}000000"
    major, minor = (int(x) for x in floor.split(".")[:2])
    return f"{major + 1}.0" if major >= 1 else f"0.{minor + 1}"


def problems(root):
    spec, sb = spec_ranges(read(root, SPEC))
    control, cb = control_ranges(read(root, CONTROL))
    p = sb + cb
    if re.search(r"plugin-hostd\s*=", read(root, SPEC)) or re.search(r"plugin-hostd \(= ", read(root, CONTROL)):
        p.append("plugin-hostd is pinned to one version: it is a range like every other dependency")
    for where, ranges in (("spec", spec), ("debian/control", control)):
        if set(ranges) != WANT:
            p.append(f"{where}: depends on {sorted(ranges)}, not {sorted(WANT)}")
        for name, (_, floor, ceiling) in ranges.items():
            if ceiling != next_ceiling(name, floor):
                p.append(f"{where}: {name} >= {floor} has the ceiling {ceiling}, not {next_ceiling(name, floor)}")
    for name in sorted(set(spec) & set(control)):
        if spec[name] != control[name]:
            p.append(f"{name}: {spec[name]} in the spec, {control[name]} in debian/control")
    return p


def planted():
    """each kind of broken range planted in a copy: every one must be seen"""
    spec, control = read(ROOT, SPEC), read(ROOT, CONTROL)
    cases = {
        "no ceiling (spec)": (SPEC, spec.replace("(omx-plugins >= 0.19.3 with omx-plugins < 0.20)", "omx-plugins >= 0.19.3")),
        "no ceiling (deb)": (CONTROL, control.replace("omx-plugins (<< 0.20~),", "")),
        "a ceiling past the next minor": (SPEC, spec.replace("omx-clap-host < 0.33)", "omx-clap-host < 0.34)")),
        "plugin-hostd pinned": (SPEC, spec.replace("Requires: (plugin-hostd >= 0.20.7 with plugin-hostd < 0.21)",
                                                    "Requires: plugin-hostd = %{version}-%{release}")),
        "the spec and the deb apart": (CONTROL, control.replace("plugin-qualify (>= 0.20.1~)", "plugin-qualify (>= 0.20.2~)")),
        "a dependency dropped": (CONTROL, control.replace("            plugin-qualification-records (>= 2026110902~), plugin-qualification-records (<< 2027000000~)\n", "").replace("omx-panel (<< 0.14~),", "omx-panel (<< 0.14~)")),
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
print("ok   plugin-hostd-full: every dependency a floor and the next minor as its ceiling, the same in the spec and debian/control")
