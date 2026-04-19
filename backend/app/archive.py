"""Read zip/tar/directory archives into an in-memory file tree."""

from __future__ import annotations

import io
import os
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass, field


@dataclass
class FileNode:
    name: str
    path: str = ""
    is_dir: bool = False
    size: int = 0
    ext: str = ""
    is_text: bool = True
    children: list[FileNode] = field(default_factory=list)
    compressed: bool = False
    archive_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "size": self.size,
            "ext": self.ext,
            "children": [c.to_dict() for c in self.children] if self.is_dir else [],
        }


class ArchiveReader:
    SKIP_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        "venv",
        ".venv",
        "dist",
        "build",
        ".eggs",
        "target",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
    }

    def read(self, path: str) -> tuple[FileNode, str]:
        lp = path.lower()
        if os.path.isdir(path):
            return self._read_dir(path), "folder"
        if lp.endswith(".zip") or lp.endswith(".whl"):
            return self._read_zip(path), "zip"
        if any(lp.endswith(e) for e in [".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".tar"]):
            return self._read_tar(path), "tar"
        try:
            return self._read_zip(path), "zip"
        except Exception:
            return self._read_tar(path), "tar"

    def _read_dir(self, root: str) -> FileNode:
        node = FileNode(name=os.path.basename(root) or root, path=root, is_dir=True)
        self._walk(root, node)
        return node

    def _walk(self, path: str, parent: FileNode, depth: int = 0) -> None:
        if depth > 20:
            return
        try:
            entries = sorted(
                os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())
            )
        except Exception:
            return
        for e in entries:
            if e.name.startswith(".") and e.name not in {".gitignore", ".env"}:
                continue
            if e.is_dir():
                if e.name in self.SKIP_DIRS:
                    continue
                child = FileNode(name=e.name, path=e.path, is_dir=True)
                parent.children.append(child)
                self._walk(e.path, child, depth + 1)
            else:
                try:
                    sz = e.stat().st_size
                except Exception:
                    sz = 0
                ext = os.path.splitext(e.name)[1].lower()
                parent.children.append(
                    FileNode(name=e.name, path=e.path, is_dir=False, size=sz, ext=ext)
                )

    def _read_zip(self, path: str) -> FileNode:
        root = FileNode(
            name=os.path.basename(path), is_dir=True, compressed=True, archive_path=path
        )
        dm: dict[str, FileNode] = {"": root}
        with zipfile.ZipFile(path, "r") as zf:
            for info in sorted(zf.infolist(), key=lambda i: i.filename):
                self._insert(dm, info.filename, info.file_size, bool(info.is_dir()), path)
        return root

    def _read_tar(self, path: str) -> FileNode:
        root = FileNode(
            name=os.path.basename(path), is_dir=True, compressed=True, archive_path=path
        )
        dm: dict[str, FileNode] = {"": root}
        with tarfile.open(path, "r:*") as tf:
            for m in sorted(tf.getmembers(), key=lambda x: x.name):
                self._insert(dm, m.name, m.size, m.isdir(), path)
        return root

    def _insert(self, dm: dict[str, FileNode], raw_path: str, size: int, is_dir: bool, archive: str) -> None:
        parts = raw_path.rstrip("/").split("/")
        cur = ""
        par = dm[""]
        for i, part in enumerate(parts):
            if not part or part == ".":
                continue
            cur = f"{cur}/{part}" if cur else part
            if cur not in dm:
                is_last = i == len(parts) - 1
                nd_is_dir = (not is_last) or is_dir
                ext = os.path.splitext(part)[1].lower() if not nd_is_dir else ""
                nd = FileNode(
                    name=part,
                    path=cur,
                    is_dir=nd_is_dir,
                    size=size if (is_last and not nd_is_dir) else 0,
                    ext=ext,
                    compressed=True,
                    archive_path=archive,
                )
                par.children.append(nd)
                dm[cur] = nd
            par = dm[cur]

    def read_text(self, node: FileNode, max_bytes: int = 500_000) -> str:
        if not node.compressed:
            with open(node.path, encoding="utf-8", errors="replace") as f:
                return f.read(max_bytes)
        lp = node.archive_path.lower()
        if lp.endswith(".zip") or lp.endswith(".whl"):
            with zipfile.ZipFile(node.archive_path) as zf:
                with zf.open(node.path) as f:
                    return f.read(max_bytes).decode("utf-8", "replace")
        with tarfile.open(node.archive_path, "r:*") as tf:
            m = tf.getmember(node.path)
            f = tf.extractfile(m)
            if not f:
                return ""
            return f.read(max_bytes).decode("utf-8", "replace")


# ── Remote archive extract (used by indexers) ────────────────────────────────

def extract_tree_from_url(url: str, filename: str | None = None) -> dict | None:
    """Download a small archive into memory and return a serializable file tree."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PackageWatcher/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read(25 * 1024 * 1024)
    except Exception:
        return None
    return extract_tree_from_bytes(data, filename or url.split("/")[-1])


def extract_tree_from_bytes(data: bytes, filename: str) -> dict | None:
    lp = filename.lower()
    files: list[dict] = []
    dirs: list[dict] = []
    try:
        if lp.endswith(".whl") or lp.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                for i in zf.infolist():
                    if i.is_dir():
                        dirs.append({"path": i.filename, "size": 0, "type": "directory"})
                    else:
                        files.append(
                            {"path": i.filename, "size": int(i.file_size), "type": "file"}
                        )
        elif any(lp.endswith(e) for e in [".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".tar"]):
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
                for m in tf.getmembers():
                    if m.isdir():
                        dirs.append({"path": m.name + "/", "size": 0, "type": "directory"})
                    elif m.isfile():
                        files.append(
                            {"path": m.name, "size": int(m.size), "type": "file"}
                        )
        else:
            return None
    except Exception:
        return None
    if not files:
        return None
    return {"files": files, "dirs": dirs, "_src_file": filename}
