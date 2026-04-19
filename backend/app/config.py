"""Static configuration: paths, providers, tuning."""

from __future__ import annotations

import os
import threading
from pathlib import Path

BASE_DIR = Path(os.environ.get("PW_DATA_DIR", Path.home() / ".package-watcher"))
DB_PATH = BASE_DIR / "packages.db"
DOWNLOAD_DIR = BASE_DIR / "downloads"

BASE_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

API_HOST = os.environ.get("PW_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("PW_PORT", "7433"))

PKG_PROVIDERS = ["PyPI", "npm", "GitHub", "Libraries.io"]
DOCKER_PROVIDERS = ["DockerHub"]
WEB_PROVIDERS = ["WebURL"]
PROVIDERS = PKG_PROVIDERS + DOCKER_PROVIDERS + WEB_PROVIDERS

BROWSER_SEMAPHORE = threading.Semaphore(4)

PROV_WORKERS: dict[str, int] = {
    "PyPI": 3,
    "npm": 8,
    "GitHub": 4,
    "DockerHub": 12,
    "Libraries.io": 2,
    "WebURL": 2,
}

PROV_DELAY: dict[str, float] = {
    "GitHub": 2.0,
    "PyPI": 0.3,
    "npm": 0.3,
    "DockerHub": 0.5,
    "Libraries.io": 0.5,
}

LANG_COLOR: dict[str, str] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Ruby": "#cc342d",
    "PHP": "#4F5D95",
    "Swift": "#ffac45",
    "Kotlin": "#A97BFF",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "C#": "#178600",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Elixir": "#6e4a7e",
    "Haskell": "#5e5086",
    "Lua": "#000080",
    "Julia": "#a270ba",
    "Zig": "#ec915c",
    "Dockerfile": "#384d54",
}

PROV_COLOR: dict[str, str] = {
    "PyPI": "#3d8bb5",
    "npm": "#cc3534",
    "GitHub": "#2ea043",
    "DockerHub": "#1d63ed",
    "Libraries.io": "#7c3aed",
    "WebURL": "#d97706",
}

MAX_PER_PAGE = 500
DEFAULT_PER_PAGE = 50
MAX_INDEX_ARCHIVE_MB = 25
DEFAULT_SCHEDULER_INTERVAL = 300
