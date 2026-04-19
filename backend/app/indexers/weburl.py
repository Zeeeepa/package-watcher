"""WebURL deep-indexer: extract article text via trafilatura."""

from __future__ import annotations

import json


def index(url: str) -> dict:
    try:
        import trafilatura
    except ImportError:
        return {"error": "trafilatura not installed"}
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"error": f"could not fetch {url}"}
        result_json = trafilatura.extract(
            downloaded,
            output_format="json",
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )
        if not result_json:
            return {"error": "trafilatura extracted nothing"}
        j = json.loads(result_json)
        text = j.get("text") or ""
        title = j.get("title") or url
        author = j.get("author") or ""
        pub_date = (j.get("date") or "")[:19]
        excerpt = (j.get("excerpt") or text[:300]).strip()
        language = j.get("language") or ""

        readme_md = f"# {title}\n\n"
        if author:
            readme_md += f"**Author:** {author}\n\n"
        if pub_date:
            readme_md += f"**Published:** {pub_date}\n\n"
        readme_md += "---\n\n" + text

        return {
            "readme_text": readme_md,
            "description": excerpt[:400],
            "author": author,
            "published_at": pub_date,
            "language": language,
            "size_bytes": len(text.encode("utf-8")),
            "file_count": 0,
            "meta_json": {"url": url, "title": title, "language": language},
            "deps_json": None,
            "versions_json": [],
            "file_tree_json": None,
        }
    except Exception as e:
        return {"error": str(e)}
