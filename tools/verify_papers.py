#!/usr/bin/env python3
"""Verify immutable PDF release packages (standard library + minisign binary).

A valid signature authenticates the manifest only relative to a trusted public
key. Publish/pin the public-key fingerprint outside GitHub as well.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS = ROOT / "publications"
PUBLIC_KEY = ROOT / "keys" / "papers.pub"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"[a-z0-9][a-z0-9._/-]*\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"v[0-9]+(?:\.[0-9]+){1,2}\Z")
SKIP = {"manifest.json", "manifest.json.minisig", "SHA256SUMS"}


class InvalidRelease(ValueError):
    pass


def require(condition: bool, why: str) -> None:
    if not condition:
        raise InvalidRelease(why)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def is_plain_release_file(path: Path, release: Path) -> bool:
    return (not path.is_symlink() and path.is_file()
            and path.resolve().is_relative_to(release.resolve()))


def verify_release(
    release: Path,
    *,
    public_key: Path = PUBLIC_KEY,
    require_signature: bool = True,
) -> dict:
    release = release.resolve()
    manifest_path = release / "manifest.json"
    require(is_plain_release_file(manifest_path, release), "missing manifest.json")

    raw = manifest_path.read_bytes()
    require(len(raw) <= 1024 * 1024, "manifest size limit exceeded")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise InvalidRelease(f"invalid JSON: {exc}") from exc

    require(isinstance(data, dict), "manifest root must be an object")
    require(set(data) == {"schema", "paper_id", "version", "title", "published_utc", "source", "files"},
            "unexpected/missing manifest fields")
    require(data["schema"] == "quendoris-papers-v1", "unsupported schema")
    require(isinstance(data["paper_id"], str) and NAME.fullmatch(data["paper_id"]) is not None
            and "/" not in data["paper_id"], "invalid paper ID")
    require(isinstance(data["version"], str) and VERSION.fullmatch(data["version"]) is not None,
            "invalid version")
    require(isinstance(data["title"], str) and data["title"].strip(), "empty title")
    require(isinstance(data["published_utc"], str)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", data["published_utc"]) is not None,
            "invalid publication UTC timestamp")

    source = data["source"]
    require(isinstance(source, dict) and set(source) == {"repository", "commit"}, "invalid source")
    require(isinstance(source["repository"], str)
            and source["repository"].startswith("https://github.com/")
            and len(source["repository"]) <= 512,
            "invalid source repository")
    require(isinstance(source["commit"], str) and COMMIT.fullmatch(source["commit"]) is not None,
            "source commit must be full 40-char lowercase SHA")

    files = data["files"]
    require(isinstance(files, list) and 1 <= len(files) <= 1000, "invalid files array")
    names: set[str] = set()
    checksums: dict[str, str] = {}
    for item in files:
        require(isinstance(item, dict) and set(item) == {"path", "sha256"}, "invalid file entry")
        name, checksum = item["path"], item["sha256"]
        require(isinstance(name, str) and NAME.fullmatch(name) is not None,
                "invalid relative asset filename")
        require(all(part not in (".", "..") for part in name.split("/"))
                and name not in SKIP and not name.startswith("."),
                "unsafe asset path")
        require(name not in names, "duplicate asset")
        require(isinstance(checksum, str) and DIGEST.fullmatch(checksum) is not None,
                "invalid SHA256 digest")
        asset = release / name
        require(is_plain_release_file(asset, release), f"missing or symlinked asset: {name}")
        require(sha256(asset) == checksum, f"SHA-256 mismatch: {name}")
        names.add(name)
        checksums[name] = checksum

    require("article.pdf" in names, "publication must contain article.pdf")
    expected_sums = "".join(f"{checksums[name]}  {name}\n" for name in sorted(names)).encode()
    sums_path = release / "SHA256SUMS"
    require(is_plain_release_file(sums_path, release), "missing SHA256SUMS")
    require(sums_path.read_bytes() == expected_sums, "SHA256SUMS does not match manifest")

    signature = release / "manifest.json.minisig"
    if require_signature:
        require(is_plain_release_file(signature, release), "missing signature")
        require(public_key.is_file(), "trusted Minisign public key not installed")
        require(shutil.which("minisign") is not None, "minisign executable missing")
        cmd = ["minisign", "-V", "-q", "-p", str(public_key),
               "-m", str(manifest_path), "-x", str(signature)]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        require(completed.returncode == 0, f"Minisign signature invalid: {completed.stderr.strip()}")

    expected_files = names | {"manifest.json", "SHA256SUMS"}
    if signature.exists():
        expected_files.add("manifest.json.minisig")
    actual = {p.relative_to(release).as_posix() for p in release.rglob("*") if p.is_file() or p.is_symlink()}
    require(actual == expected_files,
            f"unexpected/missing release files: {sorted(actual ^ expected_files)}")

    return {"status": "ok", "paper_id": data["paper_id"], "version": data["version"],
            "files_verified": len(names), "signature_verified": require_signature}


def verify_all(*, public_key: Path = PUBLIC_KEY, require_signature: bool = True) -> list[dict]:
    if not PUBLICATIONS.exists():
        return []
    require(PUBLICATIONS.is_dir() and not PUBLICATIONS.is_symlink(), "invalid publications directory")
    results = []
    seen_release_dirs = set()
    for file in sorted(PUBLICATIONS.rglob("*")):
        require(not file.is_symlink(), f"symlink forbidden in publication directory: {file}")
        if not file.is_file():
            continue
        release = file.parent
        rel = release.relative_to(PUBLICATIONS)
        require(len(rel.parts) == 3, f"file outside a paper release: {file}")
        seen_release_dirs.add(release)
    for release in sorted(seen_release_dirs):
        folder_parts = release.relative_to(PUBLICATIONS).parts
        require(release.name.startswith("v"), f"invalid version directory: {release}")
        result = verify_release(release, public_key=public_key, require_signature=require_signature)
        require(result["paper_id"] == folder_parts[1] and result["version"] == folder_parts[2],
                "manifest identity disagrees with release path")
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="verify every published version")
    parser.add_argument("--release", type=Path, help="verify one version directory")
    parser.add_argument("--public-key", type=Path, default=PUBLIC_KEY)
    parser.add_argument("--allow-unsigned", action="store_true",
                        help="local drafting only; never use for publication acceptance")
    args = parser.parse_args()
    if args.all == bool(args.release):
        parser.error("select exactly one of --all or --release")
    try:
        result = (verify_all(public_key=args.public_key,
                             require_signature=not args.allow_unsigned)
                  if args.all
                  else verify_release(args.release, public_key=args.public_key,
                                      require_signature=not args.allow_unsigned))
    except (InvalidRelease, OSError) as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
