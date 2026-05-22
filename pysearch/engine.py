from dataclasses import dataclass, field
from pathlib import Path
import re

from .scanner import read_file_safe, scan_files


@dataclass
class Match:
    file: Path
    line_number: int
    line: str
    match_start: int
    match_end: int
    context_before: list = field(default_factory=list)
    context_after: list = field(default_factory=list)


@dataclass
class SearchResult:
    file: Path
    matches: list

    @property
    def match_count(self):
        return len(self.matches)


def search_in_text(
    text: str,
    pattern: str,
    file_path: Path,
    use_regex: bool = False,
    case_sensitive: bool = False,
    context_lines: int = 0,
):
    lines = text.splitlines()
    matches = []

    try:
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled = re.compile(pattern, flags)
        else:
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled = re.compile(re.escape(pattern), flags)
    except re.error:
        return None

    for i, line in enumerate(lines):
        for m in compiled.finditer(line):
            before = lines[max(0, i - context_lines): i] if context_lines > 0 else []
            after = lines[i + 1: i + 1 + context_lines] if context_lines > 0 else []

            matches.append(Match(
                file=file_path,
                line_number=i + 1,
                line=line,
                match_start=m.start(),
                match_end=m.end(),
                context_before=before,
                context_after=after,
            ))

    return SearchResult(file=file_path, matches=matches) if matches else None


def search_files(
    root: Path,
    pattern: str,
    use_regex: bool = False,
    case_sensitive: bool = False,
    context_lines: int = 0,
    extensions: list = None,
    respect_gitignore: bool = True,
    max_results: int = None,
):
    results = []
    total_matches = 0

    for file_path in scan_files(root, extensions=extensions, respect_gitignore=respect_gitignore):
        content = read_file_safe(file_path)
        if content is None:
            continue

        result = search_in_text(
            content, pattern, file_path,
            use_regex=use_regex,
            case_sensitive=case_sensitive,
            context_lines=context_lines,
        )

        if result:
            results.append(result)
            total_matches += result.match_count

            if max_results and total_matches >= max_results:
                break

    return results