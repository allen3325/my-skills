#!/usr/bin/env python3
"""
Download and extract arXiv paper source by ID.

Usage:
    python3 download_source.py <arxiv_id> [working_dir]

Examples:
    python3 download_source.py 2401.12345
    python3 download_source.py 2401.12345v2 /home/claude/arxiv-work
    python3 download_source.py 0704.0001 /tmp/papers
"""

import os
import sys
import subprocess
import tarfile
import gzip
import shutil
import json
from pathlib import Path


def detect_and_extract(archive_path: str, extract_dir: str) -> list[str]:
    """Detect the format of the downloaded file and extract it."""

    # Try tar.gz first
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
            return [m.name for m in tar.getmembers() if m.isfile()]
    except (tarfile.TarError, gzip.BadGzipFile):
        pass

    # Try plain tar
    try:
        with tarfile.open(archive_path, "r:") as tar:
            tar.extractall(path=extract_dir)
            return [m.name for m in tar.getmembers() if m.isfile()]
    except tarfile.TarError:
        pass

    # Try gzipped single file
    try:
        with gzip.open(archive_path, "rb") as gz:
            content = gz.read()
            # Check if it looks like TeX
            if b"\\document" in content or b"\\begin" in content or b"\\section" in content:
                output_path = os.path.join(extract_dir, "main.tex")
                with open(output_path, "wb") as f:
                    f.write(content)
                return ["main.tex"]
    except (gzip.BadGzipFile, OSError):
        pass

    # Might be a plain .tex file
    try:
        with open(archive_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(2000)
        if "\\document" in content or "\\begin" in content or "\\section" in content:
            dest = os.path.join(extract_dir, "main.tex")
            shutil.copy2(archive_path, dest)
            return ["main.tex"]
    except Exception:
        pass

    raise ValueError(
        f"Could not detect format of downloaded file. "
        f"File type: {subprocess.getoutput(f'file {archive_path}')}"
    )


def find_main_tex(extract_dir: str) -> str | None:
    """Find the main .tex file (the one with \\documentclass)."""
    for root, _, files in os.walk(extract_dir):
        for fname in files:
            if fname.endswith(".tex"):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(5000)
                    if "\\documentclass" in content:
                        return os.path.relpath(fpath, extract_dir)
                except Exception:
                    continue
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 download_source.py <arxiv_id> [working_dir]")
        sys.exit(1)

    arxiv_id = sys.argv[1].strip()
    working_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/arxiv-work"

    # Clean the arxiv ID (remove URL prefix if provided)
    for prefix in ["https://arxiv.org/abs/", "http://arxiv.org/abs/",
                    "https://arxiv.org/pdf/", "arxiv.org/abs/", "arxiv:"]:
        if arxiv_id.lower().startswith(prefix.lower()):
            arxiv_id = arxiv_id[len(prefix):]
    arxiv_id = arxiv_id.strip("/").strip()

    # Create extraction directory
    safe_id = arxiv_id.replace("/", "_")
    extract_dir = os.path.join(working_dir, safe_id)
    os.makedirs(extract_dir, exist_ok=True)

    archive_path = os.path.join(extract_dir, "source_archive")

    # Download
    download_url = f"https://arxiv.org/e-print/{arxiv_id}"
    print(f"Downloading from: {download_url}")

    result = subprocess.run(
        ["curl", "-L", "-o", archive_path,
         "-H", "User-Agent: arxiv-translator/1.0",
         "--max-time", "120",
         download_url],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"ERROR: Download failed: {result.stderr}")
        sys.exit(1)

    if not os.path.exists(archive_path) or os.path.getsize(archive_path) == 0:
        print("ERROR: Downloaded file is empty or missing")
        sys.exit(1)

    # Check for HTML error page (arXiv returns HTML for invalid IDs)
    with open(archive_path, "rb") as f:
        header = f.read(500)
    if b"<!DOCTYPE" in header or b"<html" in header.lower():
        print(f"ERROR: arXiv returned an HTML page — the ID '{arxiv_id}' may be invalid or the paper may not have source files.")
        os.remove(archive_path)
        sys.exit(1)

    print(f"Downloaded: {os.path.getsize(archive_path)} bytes")

    # Extract
    try:
        files = detect_and_extract(archive_path, extract_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Clean up archive
    if os.path.exists(archive_path):
        os.remove(archive_path)

    # Find main tex file
    main_tex = find_main_tex(extract_dir)

    # Report results
    tex_files = [f for f in files if f.endswith(".tex")]
    other_files = [f for f in files if not f.endswith(".tex")]

    result = {
        "arxiv_id": arxiv_id,
        "extract_dir": extract_dir,
        "main_tex": main_tex,
        "tex_files": sorted(tex_files),
        "other_files": sorted(other_files),
        "total_files": len(files),
    }

    print("\n=== Extraction Result ===")
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    main()
