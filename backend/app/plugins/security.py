"""Cheap heuristic security signals: known-risky patterns in file names."""

from __future__ import annotations

from .base import Plugin

_RISKY = [
    "postinstall",
    "preinstall",
    "setup.py",
    "install.sh",
    ".env",
    "credentials",
    "secret",
    "token",
    "id_rsa",
    "id_dsa",
    "npm-debug.log",
]


class SecurityPlugin(Plugin):
    id = "security"
    label = "Security"

    def run(self, pkg: dict, meta: dict) -> str:
        tree = meta.get("file_tree_json") or {}
        files = tree.get("files") or []
        notes: list[str] = []
        for f in files:
            p = (f.get("path") or "").lower()
            for pat in _RISKY:
                if pat in p:
                    notes.append(f"  ⚠ {pat} → {f.get('path')}")
        if (meta.get("license_spdx") or "") == "":
            notes.append("  ⚠ No SPDX license detected")
        downloads = meta.get("meta_json", {}).get("download_stats") or {}
        if downloads and isinstance(downloads, dict):
            recent = downloads.get("last_month") or downloads.get("last_week")
            if isinstance(recent, int) and recent < 100:
                notes.append(f"  ⚠ Low recent downloads: {recent}")
        if not notes:
            return "No obvious red flags detected in file names / metadata."
        return "Potential issues:\n" + "\n".join(notes)
