"""
Reorganise MeerKLASS pipeline data directories.

For each block directory (10-digit folder, e.g. 1746662847):
  - Rename the nested <block>/<block>/ subfolder to <block>/context/
  - Create <block>/notebooks/ and move all *.ipynb files into it

The script accepts any of these input paths:
  - A single block dir:  .../BOX8/1746662847/
  - A BOX dir:           .../BOX8/
  - A pipeline dir:      .../pipeline/

Usage:
    python move_data.py <path> [--dry-run]
"""

import argparse
import re
import shutil
from pathlib import Path

# 10-digit pattern for block directory
BLOCK_RE = re.compile(r"^\d{10}$")


def is_block_dir(path: Path) -> bool:
    """Return True if *path* looks like a block directory."""
    return path.is_dir() and bool(BLOCK_RE.match(path.name))


def find_block_dirs(root: Path, max_depth: int = 3) -> list[Path]:
    """
    Recursively search *root* for block directories up to *max_depth* levels.
    Stops descending once a block directory is found (avoids entering the
    nested <block>/<block>/ subfolder).
    """
    results: list[Path] = []

    def _walk(current: Path, depth: int) -> None:
        if depth == 0:
            return
        for child in sorted(current.iterdir()):
            if not child.is_dir():
                continue
            if is_block_dir(child):
                results.append(child)
                # Don't recurse further into block dirs
            else:
                _walk(child, depth - 1)

    if is_block_dir(root):
        return [root]
    _walk(root, max_depth)
    return results


def reorganise_block(block_path: Path, dry_run: bool) -> None:
    """Reorganise a single block directory."""
    print(f"\n--- Block: {block_path} ---")

    # 1. Rename <block>/<block>/ -> <block>/context/
    nested = block_path / block_path.name
    context_path = block_path / "context"

    if context_path.exists():
        print("  SKIP  rename: 'context' already exists")
    elif not nested.exists():
        print(f"  SKIP  rename: no nested '{block_path.name}/' subfolder found")
    else:
        print(f"  Rename '{nested}' -> '{context_path}'")
        if not dry_run:
            nested.rename(context_path)

    # 2. Create notebooks/
    notebooks_path = block_path / "notebooks"
    print(f"  Create directory: {notebooks_path}")
    if not dry_run:
        notebooks_path.mkdir(exist_ok=True)

    # 3. Move *.ipynb files from block root into notebooks/
    ipynb_files = [f for f in block_path.glob("*.ipynb") if f.is_file()]
    if not ipynb_files:
        print("  No *.ipynb files found to move.")
    for nb in ipynb_files:
        dest = notebooks_path / nb.name
        if dest.exists():
            raise FileExistsError(f"Cannot move '{nb.name}': '{dest}' already exists.")
        print(f"  Move '{nb.name}' -> '{dest}'")
        if not dry_run:
            shutil.move(str(nb), str(dest))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reorganise MeerKLASS pipeline block directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python move_data.py .../pipeline/BOX8/1746662847/\n"
            "  python move_data.py .../pipeline/BOX8/\n"
            "  python move_data.py .../pipeline/\n"
            "  python move_data.py .../pipeline/ --dry-run\n"
        ),
    )
    parser.add_argument(
        "path",
        help="Block dir, BOX dir, or pipeline dir to search for block dirs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without making any changes.",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    block_dirs = find_block_dirs(root)
    if not block_dirs:
        print(f"No block directories (10-digit folders) found under: {root}")
        return

    print(
        f"Found {len(block_dirs)} block director{'y' if len(block_dirs) == 1 else 'ies'}."
    )
    if args.dry_run:
        print("[DRY RUN] No files will be moved or renamed.")

    for block in block_dirs:
        reorganise_block(block, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
