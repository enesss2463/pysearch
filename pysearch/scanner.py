from pathlib import Path
from typing import Iterator, Set
import asyncio
import aiofiles
import chardet
import pathspec

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", ".venv", "venv", "env", "dist", "build",
}

DEFAULT_BINARY_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar",
    ".gz", ".exe", ".dll", ".pyc", ".mp3", ".mp4", ".db",
}


def load_gitignore(root: Path):
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        patterns = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return None


def is_binary_file(path: Path) -> bool:
    if path.suffix.lower() in DEFAULT_BINARY_EXTENSIONS:
        return True
    try:
        chunk = path.read_bytes()[:8192]
        if b"\x00" in chunk:
            return True
        result = chardet.detect(chunk)
        return result["encoding"] is None
    except (OSError, PermissionError):
        return True


def read_file_safe(path: Path):
    try:
        raw = path.read_bytes()
        detected = chardet.detect(raw[:8192])
        encoding = detected.get("encoding") or "utf-8"
        return raw.decode(encoding, errors="replace")
    except (OSError, PermissionError):
        return None


async def read_file_async(path: Path):
    """Dosyayı async olarak okur."""
    try:
        async with aiofiles.open(path, mode="rb") as f:
            raw = await f.read()
        detected = chardet.detect(raw[:8192])
        encoding = detected.get("encoding") or "utf-8"
        return raw.decode(encoding, errors="replace")
    except (OSError, PermissionError):
        return None


def scan_files(
    root: Path,
    extensions: list = None,
    respect_gitignore: bool = True,
    skip_binary: bool = True,
) -> Iterator[Path]:
    gitignore = load_gitignore(root) if respect_gitignore else None

    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in DEFAULT_IGNORE_DIRS for part in path.parts):
            continue
        if gitignore:
            try:
                relative = path.relative_to(root)
                if gitignore.match_file(str(relative)):
                    continue
            except ValueError:
                pass
        if extensions and path.suffix.lower() not in extensions:
            continue
        if skip_binary and is_binary_file(path):
            continue
        yield path


async def scan_files_async(
    root: Path,
    extensions: list = None,
    respect_gitignore: bool = True,
) -> list:
    """Tüm dosyaları async olarak paralel okur."""
    paths = list(scan_files(root, extensions=extensions, respect_gitignore=respect_gitignore))
    tasks = [read_file_async(p) for p in paths]
    contents = await asyncio.gather(*tasks)
    return [(path, content) for path, content in zip(paths, contents) if content is not None]