# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full's dependencies, in the RPM spec and debian/control alike: every one a floor and no ceiling (owner rule
# 2026-11-16: our packages carry floors only; a breaking release stops and asks the owner). The same floors in
# both; plugin-hostd a floor like the others, never pinned to this package's own version (ruling 2026-11-09:
# plugin-hostd-full is its own repository, released last in each wave).
#
# Usage: ranges.py [root]. It first proves it sees each kind of broken dependency on a planted copy of the files.
import os, re, sys, tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SPEC, CONTROL = "packaging/plugin-hostd-full.spec", "debian/control"
WANT = {"plugin-hostd", "plugin-hostd-protocol", "omx-clap-host", "omx-plugins", "plugin-qualify", "omx-panel", "plugin-qualification-records"}


def read(root, path):
    with open(os.path.join(root, path)) as f:
        return f.read()


def spec_floors(text):
    out, bad = {}, []
    for kind, dep in re.findall(r"^(Requires|Recommends):\s*(.+)$", text, re.M):
        m = re.fullmatch(r"(\S+) >= (\S+)", dep.strip())
        if not m:
            bad.append(f"spec: {kind}: {dep.strip()} is not <name> >= <floor> (a ceiling or a pin is refused)")
            continue
        out[m.group(1)] = (kind, m.group(2))
    return out, bad


def control_floors(text):
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
                bad.append(f"debian/control: {field}: {i} is not <name> (>= <floor>~) (a ceiling or a pin is refused)")
                continue
            if mm.group(1) in seen:
                bad.append(f"debian/control: {mm.group(1)} is named twice in {field}")
            seen[mm.group(1)] = mm.group(2)
        for name, floor in seen.items():
            out[name] = (kind, floor)
    return out, bad


def problems(root):
    spec, sb = spec_floors(read(root, SPEC))
    control, cb = control_floors(read(root, CONTROL))
    p = sb + cb
    if re.search(r"plugin-hostd\s*=", read(root, SPEC)) or re.search(r"plugin-hostd \(= ", read(root, CONTROL)):
        p.append("plugin-hostd is pinned to one version: it is a floor like every other dependency")
    for where, floors in (("spec", spec), ("debian/control", control)):
        if set(floors) != WANT:
            p.append(f"{where}: depends on {sorted(floors)}, not {sorted(WANT)}")
    for name in sorted(set(spec) & set(control)):
        if spec[name] != control[name]:
            p.append(f"{name}: {spec[name]} in the spec, {control[name]} in debian/control")
    return p


def planted():
    """each kind of broken dependency planted in a copy: every one must be seen"""
    spec, control = read(ROOT, SPEC), read(ROOT, CONTROL)
    cases = {
        "a ceiling (spec)": (SPEC, spec.replace("Requires: omx-plugins >= 0.19.3",
                                                "Requires: (omx-plugins >= 0.19.3 with omx-plugins < 0.20)")),
        "a ceiling (deb)": (CONTROL, control.replace("omx-plugins (>= 0.19.3~),",
                                                     "omx-plugins (>= 0.19.3~), omx-plugins (<< 0.20~),")),
        "a ceiling past the next minor": (SPEC, spec.replace("Requires: omx-clap-host >= 0.33.0",
                                                             "Requires: omx-clap-host >= 0.33.0\nRequires: omx-clap-host < 0.34")),
        "plugin-hostd pinned": (SPEC, spec.replace("Requires: plugin-hostd >= 0.20.8",
                                                    "Requires: plugin-hostd = %{version}-%{release}")),
        "the spec and the deb apart": (CONTROL, control.replace("plugin-qualify (>= 0.20.1~)", "plugin-qualify (>= 0.20.2~)")),
        "a dependency dropped": (CONTROL, control.replace("omx-panel (>= 0.13.0~),\n            plugin-qualification-records (>= 2026110902~)",
                                                          "omx-panel (>= 0.13.0~)")),
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
print("ok   plugin-hostd-full: every dependency a floor and no ceiling, the same in the spec and debian/control")
