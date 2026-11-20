Name: plugin-hostd-full
Version: 0.20.8
Release: 1%{?dist}
License: GPL-3.0-or-later
Summary: Whole plugin host stack: daemon, workers, plugins, qualifier
URL: https://github.com/Open-Mixer/plugin-hostd-full
BuildArch: noarch

Source0: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires: make
BuildRequires: python3

# The whole plugin host stack in one install, on any Fedora: the daemon, its CLAP/LV2 worker, the OpenMixer plugins, the
# qualifier and the qualification records (one package built per architecture: the desk sets on x86_64, the Raspberry
# Pi 5 set on aarch64). Every dependency a floor at the release this one is tested with and no ceiling (owner rule
# 2026-11-16: our packages carry floors only); the records' dated version (YYYYMMDDXX) is a floor too (tests/ranges.py). The panel is a weak
# dependency: `dnf install --setopt=install_weak_deps=False plugin-hostd-full` is the headless install, with no panel.
# plugin-hostd is a floor like the others: this package is its own repository, released last in each wave (ruling
# 2026-11-09), so it never pins the daemon's own release.
Requires: plugin-hostd >= 0.20.8
Requires: plugin-hostd-protocol >= 0.7.0
Requires: omx-clap-host >= 0.33.0
Requires: omx-plugins >= 0.19.3
Requires: plugin-qualify >= 0.20.1
Recommends: omx-panel >= 0.13.0
# recommended until the package is in the channel: a hard dependency now would leave plugin-hostd-full uninstallable
Recommends: plugin-qualification-records >= 2026110902

%description
Installs plugin-hostd with everything it runs plugins with: omx-clap-host,
the CLAP worker that also runs LV2 plugins through its adapter, the OpenMixer
plugins, plugin-qualify, which measures each installed plugin before it is
trusted live, and the qualification records of this machine's class, so the
plugins measured on a machine like this one are taken from the records.

omx-panel, the plugin panels in a browser, is a weak dependency. Install with
--setopt=install_weak_deps=False for a machine with no screen.

%prep
%autosetup

%build

%install

%check
make check

%files
%license COPYING
%doc README.md

%changelog
* Thu Nov 19 2026 Pau Aliagas <linuxnow@gmail.com> - 0.20.8-1
- Pull requests since 0.20.7: #9 (the RPM and DEB builds run by workflow_dispatch
  only, make check on pull requests in lint.yml), #12 (floors only: every
  dependency a floor, no ceiling, the same in the spec and debian/control;
  tests/ranges.py refuses a ceiling or a pin), #15 (the commit-msg hook is the
  shared stub byte for byte), #17 (release.yml reads the same-pass list through
  the shared same-pass action, with tests/release_same_pass.py holding it), #19 (Fedora 45 only, the F44 cells
  dropped, and a lint refusing any F44 cell), #20 (the commit identity check is
  on for pull requests).
- Floors moved: plugin-hostd >= 0.20.8 (was 0.20.7), omx-clap-host >= 0.33.0
  (was 0.32.3); this package uses no omx-clap-core, so that floor is not set here.
- New dependency: plugin-hostd-protocol >= 0.7.0.
- Conflicts, Breaks, Replaces and Obsoletes: none, and none naming our packages.
- Unchanged floors: omx-plugins >= 0.19.3, plugin-qualify >= 0.20.1, recommended
  omx-panel >= 0.13.0 and plugin-qualification-records >= 2026110902.

* Sat Nov 14 2026 Pau Aliagas <linuxnow@gmail.com> - 0.20.7-1
- plugin-hostd-full in its own repository (ruling 2026-11-09), the outermost
  layer, released last in each wave; until now a subpackage of plugin-hostd,
  whose last build of it was 0.20.7. plugin-hostd is a range, >= 0.20.7 and
  < 0.21, like every other dependency
