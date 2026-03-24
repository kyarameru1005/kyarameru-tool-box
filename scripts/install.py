#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

APP_NAME = "kyarameru-tool-box"
MANIFEST_FILENAME = ".kyarameru_tool_box_manifest.json"
GLOBAL_AGENTS_FILENAME = "AGENTS.md"


@dataclass(frozen=True)
class InstallEntry:
    source: Path
    target: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root(root: Path | None = None) -> Path:
    base = root if root is not None else project_root()
    return base / "toolbox"


def codex_home(home: Path | None = None) -> Path:
    resolved_home = home if home is not None else Path.home()
    return resolved_home / ".codex"


def manifest_path(home: Path | None = None) -> Path:
    return codex_home(home) / MANIFEST_FILENAME


def iter_source_entries(root: Path | None = None, home: Path | None = None) -> list[InstallEntry]:
    src_root = source_root(root)
    target_root = codex_home(home)
    mappings = {
        "skills": target_root / "skills",
        "hooks": target_root / "hooks",
        "prompts": target_root / "prompts",
    }
    entries: list[InstallEntry] = []

    for key, target_base in mappings.items():
        src_dir = src_root / key
        if not src_dir.exists():
            continue
        for child in sorted(src_dir.iterdir()):
            entries.append(InstallEntry(source=child, target=target_base / child.name))

    agents_src = src_root / GLOBAL_AGENTS_FILENAME
    if agents_src.exists() and agents_src.is_file():
        entries.append(InstallEntry(source=agents_src, target=target_root / GLOBAL_AGENTS_FILENAME))

    return entries


def is_global_agents_target(path: Path) -> bool:
    return path.name == GLOBAL_AGENTS_FILENAME and path.parent.name == ".codex"


def backup_existing_agents(path: Path, dry_run: bool) -> Path | None:
    if not path.exists() and not path.is_symlink():
        return None
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak.{stamp}")
    if dry_run:
        return backup_path

    if path.is_symlink():
        target = os.readlink(path)
        backup_path.symlink_to(target)
    elif path.is_dir():
        shutil.copytree(path, backup_path)
    else:
        shutil.copy2(path, backup_path)
    return backup_path


def read_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"app": APP_NAME, "paths": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"app": APP_NAME, "paths": []}

    if not isinstance(data, dict):
        return {"app": APP_NAME, "paths": []}

    paths = data.get("paths")
    if not isinstance(paths, list):
        paths = []

    return {
        "app": data.get("app", APP_NAME),
        "paths": [str(p) for p in paths],
    }


def write_manifest(path: Path, managed_paths: Iterable[Path], dry_run: bool) -> None:
    payload = {
        "app": APP_NAME,
        "paths": sorted(str(p) for p in managed_paths),
    }
    if dry_run:
        print(f"[DRY-RUN] manifest update: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_managed(path: Path, managed_set: set[str]) -> bool:
    return str(path) in managed_set


def copy_entry(entry: InstallEntry, managed_set: set[str], dry_run: bool) -> str:
    src = entry.source
    dst = entry.target

    agents_target = is_global_agents_target(dst)
    if dst.exists() and not dst.is_symlink() and not is_managed(dst, managed_set) and not agents_target:
        return f"[SKIP] unmanaged exists: {dst}"

    backup_path: Path | None = None
    if agents_target and (dst.exists() or dst.is_symlink()):
        backup_path = backup_existing_agents(dst, dry_run)

    if dry_run:
        if backup_path is not None:
            return f"[DRY-RUN] backup+copy: {dst} -> {backup_path}, then {src} -> {dst}"
        return f"[DRY-RUN] copy: {src} -> {dst}"

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.is_symlink():
        dst.unlink()

    if src.is_dir():
        if dst.exists() and dst.is_file():
            dst.unlink()
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        if dst.exists() and dst.is_dir():
            shutil.rmtree(dst)
        shutil.copy2(src, dst)

    if backup_path is not None:
        return f"[INFO] backed up and copied: {dst} (backup: {backup_path})"
    return f"[INFO] copied: {dst}"


def link_entry(entry: InstallEntry, managed_set: set[str], dry_run: bool) -> str:
    src = entry.source
    dst = entry.target

    agents_target = is_global_agents_target(dst)
    if dst.exists() and not dst.is_symlink() and not is_managed(dst, managed_set) and not agents_target:
        return f"[SKIP] unmanaged exists: {dst}"

    backup_path: Path | None = None
    if agents_target and (dst.exists() or dst.is_symlink()):
        backup_path = backup_existing_agents(dst, dry_run)

    if dry_run:
        if backup_path is not None:
            return f"[DRY-RUN] backup+link: {dst} -> {backup_path}, then {dst} -> {src}"
        return f"[DRY-RUN] link: {dst} -> {src}"

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.is_symlink():
        if os.readlink(dst) == str(src):
            return f"[INFO] already linked: {dst}"
        dst.unlink()
    elif dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    dst.symlink_to(src)
    if backup_path is not None:
        return f"[INFO] backed up and linked: {dst} -> {src} (backup: {backup_path})"
    return f"[INFO] linked: {dst} -> {src}"


def install(mode: str, dry_run: bool, root: Path | None = None, home: Path | None = None) -> int:
    entries = iter_source_entries(root=root, home=home)
    manifest = read_manifest(manifest_path(home))
    managed_set = set(manifest.get("paths", []))

    if not entries:
        print("[WARN] no source entries found under toolbox/")
        return 0

    managed_paths: list[Path] = []
    for entry in entries:
        if mode == "copy":
            msg = copy_entry(entry, managed_set, dry_run)
        else:
            msg = link_entry(entry, managed_set, dry_run)
        print(msg)

        if msg.startswith("[INFO]") or msg.startswith("[DRY-RUN]"):
            managed_paths.append(entry.target)

    write_manifest(manifest_path(home), managed_paths, dry_run)
    return 0


def status(root: Path | None = None, home: Path | None = None) -> int:
    entries = iter_source_entries(root=root, home=home)
    if not entries:
        print("[WARN] no source entries found under toolbox/")
        return 0

    for entry in entries:
        src = entry.source
        dst = entry.target
        if dst.is_symlink():
            print(f"[LINK] {dst} -> {os.readlink(dst)}")
        elif dst.exists():
            kind = "dir" if dst.is_dir() else "file"
            print(f"[COPY] {dst} ({kind})")
        else:
            print(f"[MISS] {dst} (source: {src})")

    manifest = manifest_path(home)
    if manifest.exists():
        print(f"[INFO] manifest: {manifest}")
    else:
        print(f"[INFO] manifest missing: {manifest}")
    return 0


def uninstall(dry_run: bool, home: Path | None = None) -> int:
    mpath = manifest_path(home)
    manifest = read_manifest(mpath)
    managed_paths = [Path(p) for p in manifest.get("paths", [])]

    if not managed_paths:
        print("[WARN] no managed paths in manifest")
        return 0

    for path in sorted(managed_paths, key=lambda p: len(str(p)), reverse=True):
        if not path.exists() and not path.is_symlink():
            print(f"[SKIP] already missing: {path}")
            continue

        if dry_run:
            print(f"[DRY-RUN] remove: {path}")
            continue

        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        print(f"[INFO] removed: {path}")

    if dry_run:
        print(f"[DRY-RUN] remove manifest: {mpath}")
    elif mpath.exists():
        mpath.unlink()
        print(f"[INFO] removed manifest: {mpath}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="kyarameru-tool-box installer")
    sub = parser.add_subparsers(dest="command", required=True)

    install_cmd = sub.add_parser("install", help="Install toolbox assets")
    install_cmd.add_argument("--mode", choices=["copy", "link"], default="copy")
    install_cmd.add_argument("--dry-run", action="store_true")

    update_cmd = sub.add_parser("update", help="Re-run install")
    update_cmd.add_argument("--mode", choices=["copy", "link"], default="copy")
    update_cmd.add_argument("--dry-run", action="store_true")

    sub.add_parser("status", help="Show install status")

    uninstall_cmd = sub.add_parser("uninstall", help="Remove managed paths")
    uninstall_cmd.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command in {"install", "update"}:
        return install(mode=args.mode, dry_run=args.dry_run)
    if args.command == "status":
        return status()
    if args.command == "uninstall":
        return uninstall(dry_run=args.dry_run)

    print(f"[ERROR] unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
