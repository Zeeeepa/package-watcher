"""Download a package's archive(s) to the download directory."""

from __future__ import annotations

import json
import os
import re
import tarfile
import urllib.parse
import urllib.request
import zipfile

from . import db
from .config import DOWNLOAD_DIR
from .utils import http_get


def _dl_file(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "PackageWatcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)


def download(pkg_id: int) -> tuple[bool, str]:
    pkg = db.get_package(pkg_id)
    if not pkg:
        return False, "Not found"
    provider = pkg["provider"]
    name = pkg["name"]
    safe = re.sub(r'[/\\:*?"<>|]', "_", name)
    dest = os.path.join(str(DOWNLOAD_DIR), provider, safe)
    os.makedirs(dest, exist_ok=True)
    db.update_download(pkg_id, "downloading")
    try:
        if provider == "PyPI":
            ok, msg = _pypi(name, dest)
        elif provider == "npm":
            ok, msg = _npm(name, dest)
        elif provider == "GitHub":
            ok, msg = _github(name, dest)
        elif provider == "DockerHub":
            ok, msg = _docker(name, dest)
        else:
            ok, msg = False, "Downloads not supported for this provider"
        db.update_download(pkg_id, "done" if ok else "error", dest if ok else None)
        return ok, msg
    except Exception as e:
        db.update_download(pkg_id, "error")
        return False, str(e)


def _pypi(name: str, dest: str) -> tuple[bool, str]:
    d = http_get(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json", timeout=25)
    urls = d.get("urls") or []
    if not urls:
        return False, "No files"
    for u in urls:
        fname = u.get("filename", "")
        url = u.get("url", "")
        if fname and url:
            fp = os.path.join(dest, fname)
            if not os.path.exists(fp):
                _dl_file(url, fp)
    return True, f"{len(urls)} files"


def _npm(name: str, dest: str) -> tuple[bool, str]:
    d = http_get(
        f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='')}/latest",
        timeout=25,
    )
    tb = d.get("dist", {}).get("tarball", "")
    if not tb:
        return False, "No tarball"
    fp = os.path.join(dest, tb.split("/")[-1] or "package.tgz")
    _dl_file(tb, fp)
    try:
        with tarfile.open(fp, "r:gz") as tf:
            tf.extractall(dest)
    except Exception:
        pass
    return True, os.path.basename(fp)


def _github(name: str, dest: str) -> tuple[bool, str]:
    if "/" not in name:
        return False, "Invalid name"
    last = "Branch not found"
    for branch in ("main", "master"):
        url = f"https://github.com/{name}/archive/refs/heads/{branch}.zip"
        fp = os.path.join(dest, f"{branch}.zip")
        try:
            _dl_file(url, fp)
            with zipfile.ZipFile(fp, "r") as z:
                z.extractall(dest)
            return True, f"{branch}.zip"
        except Exception as e:
            last = str(e)
            continue
    return False, last


def _docker(name: str, dest: str) -> tuple[bool, str]:
    ns, repo = (name.split("/", 1) if "/" in name else ("library", name))
    try:
        info = http_get(f"https://hub.docker.com/v2/repositories/{ns}/{repo}/", timeout=20)
    except Exception:
        info = {"name": name}
    with open(os.path.join(dest, "image_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    return True, f"docker pull {name}"
