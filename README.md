# Stash plugin source of northwindlab

A plugin source for Stash's *Available Plugins*. It lists:

| Plugin | What it does |
|---|---|
| [Plugin Menu](https://github.com/northwindlab/stash-plugin-menu) | One icon next to Statistics with a drop-down of your plugin pages. No server needed. |
| [StashReleaseManager](https://github.com/northwindlab/stash-release-manager) | Tracks new releases of what you follow, searches your indexers and files the downloads. Needs its sidecar (a Docker container), see the project's INSTALL.md. |

## Add it to Stash

*Settings > Plugins > Available Plugins > Add Source*:

* **URL:** `https://raw.githubusercontent.com/northwindlab/stash-plugin-repo/main/index.yml`
* **Name / Local path:** anything you like (e.g. `northwindlab`)

Then tick the plugins you want under *Available Plugins* and install them. Reload plugins and the page (Ctrl+F5) afterwards.

## Maintainer notes

`python3 build.py <id>=<plugin folder> ...` zips the runtime files of a plugin whose `version:` in its own yml is not in `index.yml` yet, writes `releases/<id>-<version>.zip` and updates the entry. The zips are reproducible (fixed timestamps). Needs PyYAML. Tests: `python3 tests/test_build.py`. The plugins of this source are listed in `plugins.yml`.

## License

GNU AGPL-3.0, see [LICENSE](LICENSE). Copyright (c) 2026 northwindlab.
