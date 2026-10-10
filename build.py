#!/usr/bin/env python3
"""Builds the plugin zips and index.yml of this Stash plugin source.

  python3 build.py stash-plugin-menu=/path/to/stash-plugin-menu stash-release-manager=/path/to/plugin-folder

For every id=folder given: reads name/version from <folder>/<id>.yml, zips the runtime files (*.yml *.js *.css *.py, flat, at the zip root --
what Stash unpacks into its plugin folder) to releases/<id>-<version>.zip and writes/updates its entry in index.yml. A plugin whose version is
already in index.yml is skipped (bump `version:` in the plugin's yml first). Plugins not named keep their entry. Old zips: the newest MAX_KEEP stay.
The zips are reproducible (fixed timestamps, no owner, no path), so the same sources always give the same sha256.
Needs PyYAML (`pip install pyyaml`)."""
import datetime
import glob
import hashlib
import os
import sys
import zipfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
AUTHOR = "northwindlab"
MAX_KEEP = 3
PATTERNS = ("*.yml", "*.js", "*.css", "*.py")
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_zip(folder, dest):
    names = sorted({os.path.basename(p) for pat in PATTERNS for p in glob.glob(os.path.join(folder, pat))})
    if not names:
        raise SystemExit(f"nothing to pack in {folder}")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            with open(os.path.join(folder, name), "rb") as f:
                z.writestr(info, f.read())
    return names


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def build(sources, root=HERE, now=None):
    """sources: {id: folder}. Returns the ids that were (re)built."""
    meta = {m["id"]: m for m in load(os.path.join(root, "plugins.yml"))}
    index_path = os.path.join(root, "index.yml")
    index = load(index_path) if os.path.exists(index_path) else []
    index = [e for e in (index or []) if e.get("id")]
    os.makedirs(os.path.join(root, "releases"), exist_ok=True)
    built = []
    for pid, folder in sources.items():
        if pid not in meta:
            raise SystemExit(f"{pid} is not listed in plugins.yml")
        manifest = load(os.path.join(folder, f"{pid}.yml"))
        version = str(manifest["version"])
        have = next((e for e in index if e["id"] == pid), None)
        if have and str(have["version"]) == version:
            print(f"skip {pid} {version} (already in index.yml)")
            continue
        rel = f"releases/{pid}-{version}.zip"
        names = make_zip(folder, os.path.join(root, rel))
        entry = {
            "id": pid, "name": manifest["name"], "version": version,
            "date": (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
            "path": rel, "sha256": sha256(os.path.join(root, rel)), "requires": [],
            "metadata": {"description": meta[pid]["description"], "url": meta[pid]["url"], "tags": meta[pid].get("tags", []), "author": AUTHOR},
        }
        index = [e for e in index if e["id"] != pid] + [entry]
        built.append(pid)
        print(f"built {rel} ({len(names)} files, sha256 {entry['sha256'][:12]}…)")
        olds = sorted(glob.glob(os.path.join(root, "releases", f"{pid}-*.zip")), key=os.path.getmtime)
        for old in olds[:-MAX_KEEP]:
            os.remove(old)
    index.sort(key=lambda e: e["id"])
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(index, f, sort_keys=False, allow_unicode=True, width=100)
    return built


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    if not args:
        raise SystemExit(__doc__)
    build({k: os.path.expanduser(v) for k, v in args.items()})
