"""Tests for build.py: layout of the zip, sha256, skipping an already released version, reproducibility.  Run: python3 tests/test_build.py"""
import datetime
import hashlib
import os
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build  # noqa: E402
import yaml  # noqa: E402

FAILS = []
def check(name, cond):  # noqa: E302
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: FAILS.append(name)

root = tempfile.mkdtemp()
shutil.copy(os.path.join(os.path.dirname(__file__), "..", "plugins.yml"), root)
src = tempfile.mkdtemp()
def plugin(version):  # noqa: E302
    d = os.path.join(src, "stash-plugin-menu")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "stash-plugin-menu.yml"), "w").write(f"name: Plugin Menu\nversion: {version}\n")
    open(os.path.join(d, "stash-plugin-menu.js"), "w").write("// js\n")
    open(os.path.join(d, "stash-plugin-menu.css"), "w").write("/* css */\n")
    open(os.path.join(d, "README.md"), "w").write("not packed\n")
    os.makedirs(os.path.join(d, "tests"), exist_ok=True)
    return d
NOW = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)

d = plugin("0.1.0")
check("builds one plugin", build.build({"stash-plugin-menu": d}, root, NOW) == ["stash-plugin-menu"])
zp = os.path.join(root, "releases", "stash-plugin-menu-0.1.0.zip")
z = zipfile.ZipFile(zp)
check("files flat at the zip root, runtime files only", sorted(z.namelist()) == ["stash-plugin-menu.css", "stash-plugin-menu.js", "stash-plugin-menu.yml"])
check("no timestamps of ours, no owner", all(i.date_time == (2020, 1, 1, 0, 0, 0) for i in z.infolist()))
index = yaml.safe_load(open(os.path.join(root, "index.yml")))
e = index[0]
check("entry fields", e["id"] == "stash-plugin-menu" and e["name"] == "Plugin Menu" and e["version"] == "0.1.0" and e["path"] == "releases/stash-plugin-menu-0.1.0.zip"
      and e["date"] == "2026-01-02 03:04:05" and e["requires"] == [] and e["metadata"]["author"] == "northwindlab")
check("sha256 matches the zip", e["sha256"] == hashlib.sha256(open(zp, "rb").read()).hexdigest())
check("the version reads back as a string", isinstance(e["version"], str) and isinstance(e["sha256"], str))
check("same version again is skipped", build.build({"stash-plugin-menu": d}, root, NOW) == [])
d = plugin("0.1.1")
check("a new version replaces the entry", build.build({"stash-plugin-menu": d}, root, NOW) == ["stash-plugin-menu"] and [x["version"] for x in yaml.safe_load(open(os.path.join(root, "index.yml")))] == ["0.1.1"])
sha1 = yaml.safe_load(open(os.path.join(root, "index.yml")))[0]["sha256"]
root2 = tempfile.mkdtemp(); shutil.copy(os.path.join(os.path.dirname(__file__), "..", "plugins.yml"), root2)
build.build({"stash-plugin-menu": d}, root2, NOW)
check("reproducible: same sources, same sha256", yaml.safe_load(open(os.path.join(root2, "index.yml")))[0]["sha256"] == sha1)
try:
    build.build({"unknown-plugin": d}, root, NOW); unknown = False
except SystemExit:
    unknown = True
check("a plugin not listed in plugins.yml is refused", unknown)
print("\nALL OK" if not FAILS else f"\n{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
