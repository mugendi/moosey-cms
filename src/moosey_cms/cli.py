"""
CLI entry point for moosey-cms.

Commands:
    moosey-cms init <path>              Scaffold a new site from the example app
    moosey-cms admin [--templates DIR] Copy admin templates into your project
    moosey-cms dev  [--host H] [--port P]  Run development server (hot-reload)
    moosey-cms prod [--host H] [--port P]  Run production server
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_example_dir() -> Path:
    """Return the bundled example app directory."""
    return Path(__file__).resolve().parent.parent.parent / "example"


def get_bundled_templates_dir() -> Path:
    """Return the bundled admin templates directory."""
    return Path(__file__).resolve().parent / "_admin_templates"


def _find_main_py() -> Path:
    """Locate main.py in the current working directory."""
    p = Path.cwd() / "main.py"
    if not p.exists():
        print("Error: main.py not found in the current directory.", file=sys.stderr)
        print("Run this command from your project root, or run `moosey-cms init` first.", file=sys.stderr)
        sys.exit(1)
    return p


def _patch_main_mode(main_path: Path) -> None:
    """Patch main.py so mode is read from MOOSEY_MODE env var."""
    text = main_path.read_text(encoding="utf-8")

    # Add os import if missing
    if "import os" not in text:
        text = "import os\n" + text

    # Replace hardcoded mode with env var lookup
    text = text.replace(
        'mode="development"',
        'mode=os.environ.get("MOOSEY_MODE", "development")',
    )

    main_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    """Copy the entire example app to the target directory."""
    src = get_example_dir()
    if not src.is_dir():
        print(f"Error: bundled example directory not found at {src}", file=sys.stderr)
        sys.exit(1)

    dst = Path(args.path).resolve()

    if dst.exists() and any(dst.iterdir()):
        if not args.force:
            print(f"Error: {dst} already exists and is not empty.", file=sys.stderr)
            print("Use --force to overwrite.", file=sys.stderr)
            sys.exit(1)
        # Remove __pycache__ dirs before copying
        for cache in dst.rglob("__pycache__"):
            shutil.rmtree(cache)

    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # Patch main.py to read MOOSEY_MODE from environment
    main_py = dst / "main.py"
    if main_py.exists():
        _patch_main_mode(main_py)

    print(f"Project scaffolded to: {dst}")
    print()
    print("Next steps:")
    print(f"  cd {dst.name}")
    print("  moosey-cms dev")
    print()
    print("Visit http://localhost:8000")


def cmd_admin(args: argparse.Namespace) -> None:
    """Copy bundled admin templates into the project."""
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
    print('Add this config to your init_cms() call:')
    print()
    print('    admin={"prefix": "admin/content", "templates": "admin"}')
    print()
    print("Customize the templates in your project's templates/admin/ directory.")
    print("Then visit /admin/content/ in your browser.")


def cmd_dev(args: argparse.Namespace) -> None:
    """Run the development server with hot-reload."""
    _run_server(args, mode="development", reload=True)


def cmd_prod(args: argparse.Namespace) -> None:
    """Run the production server."""
    _run_server(args, mode="production", reload=False)


def _run_server(args: argparse.Namespace, *, mode: str, reload: bool) -> None:
    """Launch uvicorn with the given mode."""
    import uvicorn

    _find_main_py()  # ensure main.py exists

    os.environ["MOOSEY_MODE"] = mode

    reload_flag = " --reload" if reload else ""
    print(f"Starting {mode} server on http://{args.host}:{args.port}")
    print(f"  uvicorn main:app{reload_flag}")
    print()

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=reload,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="moosey-cms",
        description="Moosey CMS management CLI",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    # -- init --
    init_p = sub.add_parser("init", help="Scaffold a new site from the example app")
    init_p.add_argument("path", help="Target directory (e.g. ./my-site)")
    init_p.add_argument("--force", action="store_true", help="Overwrite if directory exists")

    # -- admin --
    admin_p = sub.add_parser("admin", help="Copy admin templates into your project")
    admin_p.add_argument(
        "--templates",
        default="./templates",
        help="Path to your project's templates directory (default: ./templates)",
    )

    # -- dev --
    dev_p = sub.add_parser("dev", help="Run development server (hot-reload)")
    dev_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    dev_p.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")

    # -- prod --
    prod_p = sub.add_parser("prod", help="Run production server")
    prod_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    prod_p.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "admin": cmd_admin,
        "dev": cmd_dev,
        "prod": cmd_prod,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
