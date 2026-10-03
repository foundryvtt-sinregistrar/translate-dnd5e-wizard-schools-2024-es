#!/usr/bin/env python3
"""Build a validated Foundry module release from an immutable Git revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT_FILES = {"module.json", "README.md", "README.en.md", "CHANGELOG.md", "LICENSE.md"}
PAYLOAD_DIRECTORIES = {"compendium", "lang", "scripts"}
SAFE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$")


def run_git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def commit_for(root: Path, reference: str) -> str:
    return run_git(root, "rev-parse", "--verify", "--end-of-options", f"{reference}^{{commit}}").decode().strip()


def manifest_for(root: Path, commit: str) -> tuple[bytes, dict]:
    raw = run_git(root, "show", f"{commit}:module.json")
    manifest = json.loads(raw)
    if not isinstance(manifest, dict):
        raise ValueError("module.json must be an object")
    if not isinstance(manifest.get("id"), str) or not SAFE_ID.fullmatch(manifest["id"]):
        raise ValueError("module.json has an invalid id")
    if not isinstance(manifest.get("version"), str) or not SAFE_VERSION.fullmatch(manifest["version"]):
        raise ValueError("module.json has an invalid version")
    return raw, manifest


def profile_for(root: Path, commit: str) -> dict:
    path = "dev-tools/buildScripts/release-profile.json"
    profile = {"archive_name": "", "manifest_channel": "latest"}
    if run_git(root, "ls-tree", "--name-only", commit, "--", path).strip():
        custom = json.loads(run_git(root, "show", f"{commit}:{path}"))
        if not isinstance(custom, dict) or custom.keys() - profile.keys():
            raise ValueError("invalid release profile")
        profile.update(custom)
    if not isinstance(profile["archive_name"], str) or (
        profile["archive_name"] and not SAFE_ID.fullmatch(profile["archive_name"])
    ):
        raise ValueError("invalid archive name in release profile")
    if profile["manifest_channel"] not in {"latest", "main"}:
        raise ValueError("invalid manifest channel in release profile")
    return profile


def verify_release(root: Path, reference: str, commit: str, manifest: dict, release_tag: str | None,
                   archive_name: str, manifest_channel: str) -> None:
    tags = []
    symbolic_ref = run_git(root, "rev-parse", "--symbolic-full-name", "--verify", "--end-of-options", reference).decode().strip()
    if symbolic_ref.startswith("refs/tags/"):
        tags.append(symbolic_ref.removeprefix("refs/tags/"))
    if release_tag:
        tags.append(release_tag.removeprefix("refs/tags/"))
    if not tags:
        return
    for tag in set(tags):
        if tag != f"v{manifest['version']}":
            raise ValueError("release tag does not match module.json version")
        if commit_for(root, f"refs/tags/{tag}") != commit:
            raise ValueError("release tag does not identify the selected commit")
    changelog = run_git(root, "show", f"{commit}:CHANGELOG.md").decode("utf-8")
    if not re.search(r"^## \[" + re.escape(manifest["version"]) + r"\](?:\s|$)", changelog, re.MULTILINE):
        raise ValueError("release version is absent from CHANGELOG.md")
    repository = manifest.get("url")
    if not isinstance(repository, str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("module.json url must be a GitHub repository URL")
    expected_manifest = (
        f"{repository}/releases/latest/download/module.json"
        if manifest_channel == "latest"
        else repository.replace("https://github.com/", "https://raw.githubusercontent.com/") + "/main/module.json"
    )
    if manifest.get("manifest") != expected_manifest:
        raise ValueError("module.json manifest does not match the publication channel")
    expected_download = f"{repository}/releases/download/v{manifest['version']}/{archive_name}.zip"
    if manifest.get("download") != expected_download:
        raise ValueError("module.json download does not match the versioned release ZIP")


def validate_archive(path: Path, raw_manifest: bytes, manifest: dict) -> bytes:
    prefix = manifest["id"] + "/"
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP checksum validation failed")
        files = set()
        for entry in archive.infolist():
            if not entry.filename.startswith(prefix):
                raise ValueError(f"unexpected archive prefix: {entry.filename}")
            relative = entry.filename[len(prefix):]
            if not relative:
                continue
            normalized = relative.rstrip("/")
            parts = normalized.split("/")
            if "\\" in relative or any(part in {"", ".", ".."} for part in parts):
                raise ValueError(f"unsafe archive path: {entry.filename}")
            if relative not in ROOT_FILES and parts[0] not in PAYLOAD_DIRECTORIES:
                raise ValueError(f"non-distributable file in archive: {relative}")
            if entry.is_dir():
                continue
            if relative in files:
                raise ValueError(f"duplicate archive file: {relative}")
            files.add(relative)
            if relative.endswith(".json"):
                json.loads(archive.read(entry))
        missing = ROOT_FILES - files
        if missing:
            raise ValueError("missing release files: " + ", ".join(sorted(missing)))
        archived_manifest = archive.read(prefix + "module.json")
        if archived_manifest.replace(b"\r\n", b"\n") != raw_manifest.replace(b"\r\n", b"\n"):
            raise ValueError("archived module.json differs from the selected commit")
        for path_name in [*manifest.get("esmodules", []), *(item["path"] for item in manifest.get("languages", []))]:
            if path_name not in files:
                raise ValueError(f"manifest entry is missing from archive: {path_name}")
        return archived_manifest


def build(arguments: argparse.Namespace) -> tuple[str, list[Path]]:
    root = Path(run_git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    if not arguments.allow_dirty and run_git(root, "status", "--porcelain").strip():
        raise ValueError("working tree is not clean; commit changes or use --allow-dirty")
    commit = commit_for(root, arguments.ref)
    raw_manifest, manifest = manifest_for(root, commit)
    profile = profile_for(root, commit)
    archive_name = arguments.name or profile["archive_name"] or manifest["id"]
    if not SAFE_ID.fullmatch(archive_name):
        raise ValueError("invalid output archive name")
    verify_release(root, arguments.ref, commit, manifest, arguments.release_tag, archive_name, profile["manifest_channel"])
    output = (root / arguments.dist).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".build-", dir=output) as temporary:
        stage = Path(temporary)
        versioned = stage / f"{archive_name}-{manifest['version']}.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--prefix={manifest['id']}/", "-o", str(versioned), commit], cwd=root, check=True)
        archived_manifest = validate_archive(versioned, raw_manifest, manifest)
        alias = stage / f"{archive_name}.zip"
        shutil.copyfile(versioned, alias)
        external_manifest = stage / "module.json"
        external_manifest.write_bytes(archived_manifest)
        artifacts = [versioned, alias, external_manifest]
        checksum = stage / "SHA256SUMS.txt"
        checksum.write_text("".join(f"{hashlib.sha256(item.read_bytes()).hexdigest()}  {item.name}\n" for item in artifacts), encoding="ascii")
        artifacts.append(checksum)
        results = []
        for artifact in artifacts:
            destination = output / artifact.name
            artifact.replace(destination)
            results.append(destination)
    return commit, results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--release-tag")
    parser.add_argument("--name", default="")
    parser.add_argument("--allow-dirty", action="store_true")
    arguments = parser.parse_args()
    try:
        commit, artifacts = build(arguments)
        print(f"Commit: {commit}")
        for artifact in artifacts:
            print(f"OK: {artifact} ({artifact.stat().st_size} bytes)")
        return 0
    except subprocess.CalledProcessError as error:
        print(f"ERROR (git): {error.stderr.decode('utf-8', errors='replace').strip()}", file=sys.stderr)
    except (KeyError, OSError, TypeError, ValueError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
