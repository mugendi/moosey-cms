"""
CLI entry point for moosey-cms.

Usage:
    moosey-cms setup --templates ./templates
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_bundled_templates_dir() -> Path:
    return Path(__file__).resolve().parent / "_admin_templates"


def cmd_setup(args: argparse.Namespace) -> None:
    src = get_bundled_templates_dir()
    if not src.is_dir():
        print(f"Error: bundled templates directory not found at {src}", file=sys.stderr)
        sys.exit(1)

    dst = Path(args.templates).resolve() / "admin"
    dst.mkdir(parents=True, exist_ok=True)

    files = sorted(src.iterdir())
    for f in files:
        if f.is_file():
            shutil.copy2(f, dst / f.name)
            print(f"  Created: {dst / f.name}")

    print()
    print("Admin templates installed successfully.")
    print()
    print("Add this config to your init_cms() call:")
    print()
    print('    admin={"prefix": "admin/content", "templates": "admin"}')
    print()
    print("Customize the templates in your project's templates/admin/ directory.")
    print("Then visit /admin/content/ in your browser.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="moosey-cms", description="Moosey CMS management CLI")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    setup_parser = sub.add_parser("setup", help="Scaffold admin templates into your project")
    setup_parser.add_argument(
        "--templates",
        default="./templates",
        help="Path to your project's templates directory (default: ./templates)",
    )

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)


if __name__ == "__main__":
    main()
