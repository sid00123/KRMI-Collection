#!/usr/bin/env python3
"""Utility to clone infantry gfx/asset files for a new country tag.

Typical usage (from the mod root):

    python tools/generate_infantry_assets.py LIT --template-tag BLR

This copies `zzz_BLR_infantry.gfx`/`.asset` to LIT variants and updates
country/entity tags along the way. Use --dry-run to preview the changes.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

TemplateFiles = Sequence[Tuple[str, str]]
DEFAULT_FILES: TemplateFiles = (
    ("gfx/entities/zzz_{tag}_infantry.gfx", "Infantry gfx"),
    ("gfx/entities/zzz_{tag}_infantry_asset.asset", "Infantry asset"),
)


def _detect_default_mod_root() -> Path:
    candidates = []
    cwd = Path.cwd().resolve()
    candidates.append(cwd)

    exe_path = Path(sys.argv[0]).resolve()
    candidates.append(exe_path.parent)
    candidates.append(exe_path.parent.parent)

    for candidate in candidates:
        if not candidate:
            continue
        if (candidate / "gfx").is_dir():
            return candidate

    return cwd


DEFAULT_MOD_ROOT = _detect_default_mod_root()


def _prompt_bool(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{prompt} {suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def _prompt_for_args() -> List[str]:
    print("Interactive mode — press Ctrl+C to cancel. Leave a field blank to accept the default.")

    def _ask_tag(label: str, default: str | None = None) -> str:
        while True:
            raw = input(f"{label}{f' [{default}]' if default else ''}: ").strip()
            if raw:
                return raw
            if default:
                return default
            print("Please enter a three-letter tag.")

    new_tag = _ask_tag("New country tag", None).upper()
    template_tag = _ask_tag("Template tag", "BLR").upper()
    default_root = str(DEFAULT_MOD_ROOT)
    mod_root = input(f"Mod root [{default_root}]: ").strip() or default_root
    mesh_prefix = input(f"Mesh prefix [MI_{new_tag}]: ").strip()

    args: List[str] = [new_tag]
    if template_tag:
        args.extend(["--template-tag", template_tag])
    if mod_root != ".":
        args.extend(["--mod-root", mod_root])
    if mesh_prefix:
        args.extend(["--mesh-prefix", mesh_prefix])

    while True:
        extra = input("Extra replacement (FROM=TO, blank to finish): ").strip()
        if not extra:
            break
        args.extend(["--extra-replace", extra])

    if _prompt_bool("Preview only (dry run)?", default=False):
        args.append("--dry-run")
    if _prompt_bool("Overwrite existing files if present?", default=False):
        args.append("--force")

    return args


def _validate_tag(value: str) -> str:
    tag = value.strip().upper()
    if len(tag) != 3 or not tag.isalpha():
        raise argparse.ArgumentTypeError(
            f"Country tags must be three alphabetic characters (got '{value}')."
        )
    return tag


def _parse_replacement(value: str) -> Tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Extra replacements must look like FROM=TO")
    old, new = value.split("=", 1)
    if not old:
        raise argparse.ArgumentTypeError("Replacement source cannot be empty")
    return old, new


def _apply_replacements(
    content: str,
    replacements: Iterable[Tuple[str, str]],
    template_tag: str,
    mesh_prefix: str | None,
) -> str:
    placeholder = None
    token = f"MI_{template_tag}"
    if mesh_prefix is not None:
        placeholder = f"__MESH_{uuid.uuid4().hex}__"
        content = content.replace(token, placeholder)

    for old, new in replacements:
        content = content.replace(old, new)

    if mesh_prefix is not None and placeholder is not None:
        content = content.replace(placeholder, mesh_prefix)

    return content


def _build_replacements(template_tag: str, new_tag: str, extras: List[Tuple[str, str]]):
    base = [
        (f"zzz_{template_tag}_", f"zzz_{new_tag}_"),
        (f"{template_tag}_", f"{new_tag}_"),
        (f"{template_tag.lower()}_", f"{new_tag.lower()}_"),
        (template_tag.lower(), new_tag.lower()),
        (template_tag, new_tag),
    ]
    base.extend(extras)
    return base


def clone_files(
    template_tag: str,
    new_tag: str,
    mod_root: Path,
    files: TemplateFiles,
    replacements: List[Tuple[str, str]],
    mesh_prefix: str | None,
    dry_run: bool,
    force: bool,
) -> None:
    for pattern, label in files:
        src = mod_root / pattern.format(tag=template_tag)
        dst = mod_root / pattern.format(tag=new_tag)

        if not src.exists():
            raise FileNotFoundError(f"Template file '{src}' not found")
        if dst.exists() and not force and not dry_run:
            raise FileExistsError(
                f"Target file '{dst}' already exists (use --force to overwrite)"
            )

        text = src.read_text(encoding="utf-8")
        updated = _apply_replacements(text, replacements, template_tag, mesh_prefix)

        if dry_run:
            print(f"[dry-run] Would write {label}: {dst}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(updated, encoding="utf-8")
        print(f"Created {label}: {dst}")


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = _prompt_for_args()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_tag", type=_validate_tag, help="Three-letter country tag to generate (e.g., LIT)")
    parser.add_argument("--template-tag", default="BLR", type=_validate_tag, help="Source country tag to copy from (default: BLR)")
    parser.add_argument(
        "--mod-root",
        default=str(DEFAULT_MOD_ROOT),
        help=f"Path to the mod root (default: {DEFAULT_MOD_ROOT})",
    )
    parser.add_argument(
        "--mesh-prefix",
        dest="mesh_prefix",
        help="Value that should replace occurrences of MI_<TEMPLATE>. Default derives from the new tag; set to MI_<TEMPLATE> to keep original meshes.",
    )
    parser.add_argument(
        "--extra-replace",
        action="append",
        default=[],
        type=_parse_replacement,
        metavar="FROM=TO",
        help="Additional literal replacements applied after the automatic ones",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute file contents without writing changes")
    parser.add_argument("--force", action="store_true", help="Overwrite targets if they already exist")

    args = parser.parse_args(argv)

    mod_root = Path(args.mod_root).expanduser().resolve()
    if not mod_root.exists():
        parser.error(f"Mod root '{mod_root}' does not exist")

    mesh_prefix = args.mesh_prefix or f"MI_{args.new_tag}"
    replacements = _build_replacements(args.template_tag, args.new_tag, args.extra_replace)

    try:
        clone_files(
            template_tag=args.template_tag,
            new_tag=args.new_tag,
            mod_root=mod_root,
            files=DEFAULT_FILES,
            replacements=replacements,
            mesh_prefix=mesh_prefix,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (FileNotFoundError, FileExistsError) as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
