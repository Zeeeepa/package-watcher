"""GitHub deep-indexer: repo info + README + dep files + release versions via API."""

from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request

from ..utils import http_get, http_get_text


def _api(url: str, timeout: int = 20) -> dict:
    return http_get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=timeout,
    )


def _raw(repo: str, branch: str, path: str) -> str:
    try:
        return http_get_text(
            f"https://raw.githubusercontent.com/{repo}/{branch}/{path}",
            timeout=10,
            max_bytes=200_000,
        )
    except Exception:
        return ""


def _parse_deps(files_on_root: set[str], repo: str, branch: str) -> dict | None:
    deps: list[str] = []
    dev_deps: list[str] = []

    if "requirements.txt" in files_on_root:
        for line in _raw(repo, branch, "requirements.txt").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps.append(line)
    if "package.json" in files_on_root:
        try:
            pj = json.loads(_raw(repo, branch, "package.json"))
            deps += list((pj.get("dependencies") or {}).keys())
            dev_deps += list((pj.get("devDependencies") or {}).keys())
        except Exception:
            pass
    if "pyproject.toml" in files_on_root:
        raw = _raw(repo, branch, "pyproject.toml")
        in_deps = False
        for line in raw.splitlines():
            line = line.strip()
            if line == "[tool.poetry.dependencies]":
                in_deps = True
            elif line.startswith("[") and in_deps:
                break
            elif in_deps and "=" in line:
                pkg = line.split("=")[0].strip().strip('"').strip("'")
                if pkg and pkg.lower() != "python":
                    deps.append(pkg)
    if not deps and not dev_deps:
        return None
    return {"dependencies": deps, "dev_deps": dev_deps, "peer_deps": []}


def index(repo: str) -> dict:
    if "/" not in repo:
        return {"error": "repo must be owner/name"}

    info = _api(f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}")
    branch = info.get("default_branch") or "main"

    readme_text = ""
    try:
        rdata = _api(
            f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}/readme"
        )
        if rdata.get("content"):
            readme_text = base64.b64decode(rdata["content"]).decode("utf-8", "replace")
    except Exception:
        for fname in ("README.md", "readme.md", "README.rst"):
            readme_text = _raw(repo, branch, fname)
            if readme_text:
                break

    tree = None
    file_count = 0
    root_files: set[str] = set()
    try:
        tree_data = _api(
            f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}/git/trees/{branch}?recursive=1",
            timeout=30,
        )
        nodes = tree_data.get("tree") or []
        files = []
        dirs = []
        for n in nodes:
            path = n.get("path") or ""
            if n.get("type") == "blob":
                files.append({"path": path, "size": int(n.get("size") or 0), "type": "file"})
                if "/" not in path:
                    root_files.add(path)
            elif n.get("type") == "tree":
                dirs.append({"path": path + "/", "size": 0, "type": "directory"})
        if files:
            tree = {"files": files, "dirs": dirs, "_src_file": f"GitHub API ({branch})"}
            file_count = len(files)
    except Exception:
        pass

    deps_json = _parse_deps(root_files, repo, branch) if root_files else None

    versions = []
    try:
        releases = _api(
            f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}/releases?per_page=30"
        )
        for r in releases or []:
            versions.append(
                {
                    "version": r.get("tag_name") or r.get("name") or "",
                    "date": (r.get("published_at") or r.get("created_at") or "")[:19],
                    "url": r.get("html_url") or "",
                    "size": 0,
                }
            )
    except Exception:
        pass

    topics = info.get("topics") or []

    return {
        "readme_text": readme_text,
        "deps_json": deps_json,
        "versions_json": versions,
        "file_tree_json": tree,
        "meta_json": {
            "stars": int(info.get("stargazers_count") or 0),
            "forks": int(info.get("forks_count") or 0),
            "open_issues": int(info.get("open_issues_count") or 0),
            "license": (info.get("license") or {}).get("spdx_id", "") or "",
            "homepage": info.get("homepage") or "",
            "branch": branch,
            "topics": topics,
        },
        "description": info.get("description") or "",
        "language": info.get("language") or "",
        "size_bytes": int(info.get("size") or 0) * 1024,
        "file_count": file_count,
        "published_at": (info.get("pushed_at") or info.get("updated_at") or "")[:19],
        "author": (info.get("owner") or {}).get("login", ""),
        "stars": int(info.get("stargazers_count") or 0),
        "forks": int(info.get("forks_count") or 0),
        "open_issues": int(info.get("open_issues_count") or 0),
        "license_spdx": (info.get("license") or {}).get("spdx_id", "") or "",
        "homepage": info.get("homepage") or "",
        "topics_json": topics,
    }
