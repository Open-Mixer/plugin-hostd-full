# SPDX-License-Identifier: GPL-3.0-or-later
# plugin-hostd-full's dependencies, in the RPM spec and debian/control alike: no typed version on any of them (owner
# ruling 2026-11-24: no hand-kept floors; each layer builds and installs against the lower layer's published package),
# and the same packages, Requires/Depends and Recommends alike, in both.
#
# Usage: deps.py [root]. It first proves it sees each kind of broken dependency on a planted copy of the files.
import os, re, sys, tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SPEC, CONTROL = "packaging/plugin-hostd-full.spec", "debian/control"
WANT = {"plugin-hostd", "plugin-hostd-protocol", "omx-clap-host", "omx-plugins", "plugin-qualify", "omx-panel", "plugin-qualification-records"}


def read(root, path):
    with open(os.path.join(root, path)) as f:
        return f.read()


def spec_deps(text):
    out, bad = {}, []
    for kind, dep in re.findall(r"^(Requires|Recommends):\s*(.+)$", text, re.M):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+._-]*", dep.strip()):
            bad.append(f"spec: {kind}: {dep.strip()} carries a version (a typed floor, ceiling or pin is refused)")
            continue
        out[dep.strip()] = kind
    return out, bad


def control_deps(text):
    stanza = text[text.index("Package: plugin-hostd-full"):].split("\n\n")[0]
    out, bad = {}, []
    for field, kind in (("Depends", "Requires"), ("Recommends", "Recommends")):
        m = re.search(rf"^{field}:((?:.*\n)(?:[ \t].*\n)*)", stanza + "\n", re.M)
        if not m:
            continue
        items = [i.strip() for i in m.group(1).replace("\n", " ").split(",") if i.strip() and not i.strip().startswith("${")]
        for i in items:
            if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", i):
                bad.append(f"debian/control: {field}: {i} carries a version (a typed floor, ceiling or pin is refused)")
                continue
            if i in out:
                bad.append(f"debian/control: {i} is named twice")
            out[i] = kind
    return out, bad


def problems(root):
    spec, sb = spec_deps(read(root, SPEC))
    control, cb = control_deps(read(root, CONTROL))
    p = sb + cb
    for where, deps in (("spec", spec), ("debian/control", control)):
        if set(deps) != WANT:
            p.append(f"{where}: depends on {sorted(deps)}, not {sorted(WANT)}")
    for name in sorted(set(spec) & set(control)):
        if spec[name] != control[name]:
            p.append(f"{name}: {spec[name]} in the spec, {control[name]} in debian/control")
    return p


def planted():
    """each kind of broken dependency planted in a copy: every one must be seen"""
    spec, control = read(ROOT, SPEC), read(ROOT, CONTROL)
    cases = {
        "a floor (spec)": (SPEC, spec.replace("Requires: omx-plugins\n", "Requires: omx-plugins >= 0.19.3\n")),
        "a floor (deb)": (CONTROL, control.replace("omx-plugins,", "omx-plugins (>= 0.19.3~),")),
        "a ceiling (spec)": (SPEC, spec.replace("Requires: omx-clap-host\n",
                                                "Requires: (omx-clap-host with omx-clap-host < 0.34)\n")),
        "plugin-hostd pinned": (SPEC, spec.replace("Requires: plugin-hostd\n",
                                                    "Requires: plugin-hostd = %{version}-%{release}\n")),
        "a dated records floor (deb)": (CONTROL, control.replace("plugin-qualification-records",
                                                                 "plugin-qualification-records (>= 2026110902~)")),
        "the spec and the deb apart": (CONTROL, control.replace("Recommends: omx-panel,\n            plugin-qualification-records",
                                                                "Recommends: plugin-qualification-records")
                                                       .replace("plugin-qualify,", "plugin-qualify,\n         omx-panel,")),
        "a dependency dropped": (CONTROL, control.replace("Recommends: omx-panel,\n            plugin-qualification-records",
                                                          "Recommends: omx-panel")),
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
    print("deps: the check does not see " + "; ".join(missed))
    sys.exit(2)
p = problems(ROOT)
for line in p:
    print("FAIL " + line)
if p:
    sys.exit(1)
print("ok   plugin-hostd-full: no dependency carries a typed version, the same packages in the spec and debian/control")
