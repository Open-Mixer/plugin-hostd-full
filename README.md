# plugin-hostd-full

The whole plugin host stack in one install: plugin-hostd (the daemon), omx-clap-host (the CLAP worker that also runs
LV2 plugins through its adapter), the OpenMixer plugins, plugin-qualify (which measures each installed plugin before it
is trusted live) and the qualification records of this machine's class. omx-panel, the plugin panels in a browser, is a
weak dependency.

    sudo dnf install plugin-hostd-full
    sudo apt install plugin-hostd-full

With no screen: `sudo dnf install --setopt=install_weak_deps=False plugin-hostd-full`, or
`sudo apt install --no-install-recommends plugin-hostd-full`.

This repository is the package alone: every dependency with a floor and a ceiling (`make check`), the outermost layer of
each release wave, released last. Until 1.0.0 it was a subpackage of plugin-hostd.

GPL-3.0-or-later. See [COPYING](COPYING).
