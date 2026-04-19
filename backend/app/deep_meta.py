"""Deep metadata: fetch live registry info for the detail panel."""

from __future__ import annotations

import urllib.parse

from .utils import http_get


def fetch_meta(provider: str, name: str) -> dict:
    try:
        if provider == "PyPI":
            return _pypi(name)
        if provider == "npm":
            return _npm(name)
        if provider == "GitHub":
            return _github(name)
        if provider == "DockerHub":
            return _docker(name)
        return {"error": f"No deep-fetch for {provider}"}
    except Exception as e:
        return {"error": str(e)}


def _pypi(name: str) -> dict:
    d = http_get(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json", timeout=25)
    info = d.get("info") or {}
    urls = d.get("urls") or []
    releases = d.get("releases") or {}
    versions = []
    for ver, files in releases.items():
        if not files:
            continue
        dates = [f.get("upload_time_iso_8601", "") for f in files if f.get("upload_time_iso_8601")]
        versions.append(
            {
                "version": ver,
                "date": (min(dates) if dates else "")[:19],
                "size": sum(f.get("size", 0) for f in files),
                "file_count": len(files),
                "yanked": any(f.get("yanked") for f in files),
            }
        )
    versions.sort(key=lambda v: v["date"], reverse=True)

    downloads = {}
    try:
        ds = http_get(
            f"https://pypistats.org/api/packages/{urllib.parse.quote(name)}/recent",
            timeout=15,
        )
        downloads = ds.get("data") or {}
    except Exception:
        pass

    readme = info.get("description", "") or ""
    if len(readme) > 200_000:
        readme = readme[:200_000] + "\n\n…(truncated)"
    kw = info.get("keywords") or ""
    return {
        "name": info.get("name", name),
        "version": info.get("version", ""),
        "description": info.get("summary", ""),
        "author": info.get("author", ""),
        "author_email": info.get("author_email", ""),
        "homepage": info.get("home_page", "") or info.get("project_url", ""),
        "license": info.get("license", ""),
        "url": f"https://pypi.org/project/{name}/",
        "published_at": urls[0].get("upload_time_iso_8601", "") if urls else "",
        "size_bytes": sum(u.get("size", 0) for u in urls) or None,
        "file_count": len(urls) or None,
        "language": "Python",
        "keywords": [k.strip() for k in kw.replace(",", " ").split() if k.strip()],
        "dependencies": info.get("requires_dist") or [],
        "dev_deps": [],
        "peer_deps": [],
        "classifiers": info.get("classifiers") or [],
        "versions": versions[:40],
        "download_stats": downloads,
        "readme": readme,
        "requires_python": info.get("requires_python", ""),
        "project_urls": info.get("project_urls") or {},
        "error": None,
    }


def _npm(name: str) -> dict:
    enc = urllib.parse.quote(name, safe="@")
    d = http_get(f"https://registry.npmjs.org/{enc}", timeout=25)
    dist_tags = d.get("dist-tags") or {}
    latest = dist_tags.get("latest", "")
    all_vers = d.get("versions") or {}
    v = all_vers.get(latest) or {}
    dist = v.get("dist") or {}
    times = d.get("time") or {}
    versions = []
    for ver, meta in all_vers.items():
        dd = meta.get("dist") or {}
        versions.append(
            {
                "version": ver,
                "date": (times.get(ver, "") or "")[:19],
                "size": dd.get("unpackedSize", 0),
            }
        )
    versions.sort(key=lambda x: x["date"], reverse=True)
    return {
        "name": name,
        "version": latest,
        "description": (d.get("description") or v.get("description", "")).strip(),
        "author": (v.get("author") or {}).get("name", "") if isinstance(v.get("author"), dict) else str(v.get("author", "")),
        "homepage": v.get("homepage", ""),
        "license": v.get("license", ""),
        "keywords": v.get("keywords") or [],
        "dependencies": list((v.get("dependencies") or {}).keys()),
        "dev_deps": list((v.get("devDependencies") or {}).keys()),
        "peer_deps": list((v.get("peerDependencies") or {}).keys()),
        "versions": versions[:40],
        "size_bytes": dist.get("unpackedSize"),
        "file_count": dist.get("fileCount"),
        "language": "JavaScript",
        "published_at": (times.get(latest, "") or "")[:19],
        "readme": (v.get("readme") or d.get("readme") or "").strip(),
        "error": None,
    }


def _github(repo: str) -> dict:
    if "/" not in repo:
        return {"error": "repo must be owner/name"}
    try:
        info = http_get(
            f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=20,
        )
    except Exception as e:
        return {"error": str(e)}
    versions = []
    try:
        releases = http_get(
            f"https://api.github.com/repos/{urllib.parse.quote(repo, safe='/')}/releases?per_page=30",
            headers={"Accept": "application/vnd.github+json"},
            timeout=20,
        )
        for r in releases or []:
            versions.append(
                {
                    "version": r.get("tag_name") or "",
                    "date": (r.get("published_at") or "")[:19],
                    "size": 0,
                    "url": r.get("html_url") or "",
                }
            )
    except Exception:
        pass
    return {
        "name": repo,
        "description": info.get("description") or "",
        "author": (info.get("owner") or {}).get("login", ""),
        "homepage": info.get("homepage") or "",
        "license": (info.get("license") or {}).get("spdx_id", "") or "",
        "url": info.get("html_url") or f"https://github.com/{repo}",
        "stars": int(info.get("stargazers_count") or 0),
        "forks": int(info.get("forks_count") or 0),
        "open_issues": int(info.get("open_issues_count") or 0),
        "language": info.get("language") or "",
        "topics": info.get("topics") or [],
        "size_bytes": int(info.get("size") or 0) * 1024,
        "published_at": (info.get("pushed_at") or info.get("updated_at") or "")[:19],
        "versions": versions,
        "dependencies": [],
        "error": None,
    }


def _docker(name: str) -> dict:
    ns, repo = (name.split("/", 1) if "/" in name else ("library", name))
    info = http_get(f"https://hub.docker.com/v2/repositories/{ns}/{repo}/", timeout=20)
    tags_data = http_get(
        f"https://hub.docker.com/v2/repositories/{ns}/{repo}/tags?page_size=30",
        timeout=20,
    )
    versions = []
    for t in tags_data.get("results", []) or []:
        sz = sum(img.get("size", 0) for img in t.get("images") or [])
        versions.append(
            {
                "version": t.get("name", "") or "",
                "date": (t.get("last_updated", "") or "")[:19],
                "size": sz,
            }
        )
    return {
        "name": name,
        "description": info.get("description") or "",
        "author": ns,
        "url": f"https://hub.docker.com/r/{name}" if "/" in name else f"https://hub.docker.com/_/{name}",
        "pull_count": int(info.get("pull_count") or 0),
        "stars": int(info.get("star_count") or 0),
        "size_bytes": int(info.get("full_size") or 0),
        "published_at": (info.get("last_updated", "") or "")[:19],
        "versions": versions,
        "readme": info.get("full_description") or "",
        "dependencies": [],
        "error": None,
    }
