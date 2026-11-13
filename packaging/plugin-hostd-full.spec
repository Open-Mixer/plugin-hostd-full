Name: plugin-hostd-full
Version: 1.0.0
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
# Pi 5 set on aarch64). Every dependency a floor at the release this one is tested with and a ceiling below the next
# minor; the records' dated version (YYYYMMDDXX) below the next year's first (tests/ranges.py). The panel is a weak
# dependency: `dnf install --setopt=install_weak_deps=False plugin-hostd-full` is the headless install, with no panel.
# plugin-hostd is a range like the others: this package is its own repository, released last in each wave (ruling
# 2026-11-09), so it never pins the daemon's own release.
Requires: (plugin-hostd >= 0.20.7 with plugin-hostd < 0.21)
Requires: (omx-clap-host >= 0.32.3 with omx-clap-host < 0.33)
Requires: (omx-plugins >= 0.19.3 with omx-plugins < 0.20)
Requires: (plugin-qualify >= 0.20.1 with plugin-qualify < 0.21)
Recommends: (omx-panel >= 0.13.0 with omx-panel < 0.14)
# recommended until the package is in the channel: a hard dependency now would leave plugin-hostd-full uninstallable
Recommends: (plugin-qualification-records >= 2026110902 with plugin-qualification-records < 2027000000)

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
* Fri Nov 13 2026 Pau Aliagas <linuxnow@gmail.com> - 1.0.0-1
- plugin-hostd-full in its own repository (ruling 2026-11-09), the outermost
  layer, released last in each wave; until now a subpackage of plugin-hostd,
  whose last build of it was 0.20.7. plugin-hostd is a range, >= 0.20.7 and
  < 0.21, like every other dependency
