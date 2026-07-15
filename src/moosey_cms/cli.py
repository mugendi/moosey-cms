"""
CLI entry point for moosey-cms.

Commands:
    moosey-cms init <path>              Scaffold a new site from the example app
    moosey-cms config [--force]         Initialize or update config for existing project
    moosey-cms admin [--templates DIR]  Copy admin templates into your project
    moosey-cms dev  [--host H] [--port P]  Run development server (hot-reload)
    moosey-cms prod [--host H] [--port P]  Run production server
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

import questionary

from .lib.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, CacheConfig, save_config
from .lib.crypto import generate_key

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_example_dir() -> Path:
    """Return the bundled example app directory."""
    return Path(__file__).resolve().parent.parent.parent / "example"


def get_bundled_templates_dir() -> Path:
    """Return the bundled admin templates directory."""
    return Path(__file__).resolve().parent / "_admin_templates"


def get_bundled_static_dir() -> Path:
    """Return the bundled admin static files directory."""
    return Path(__file__).resolve().parent / "_static" / "admin"


def _find_main_py() -> Path:
    """Locate main.py in the current working directory."""
    p = Path.cwd() / "main.py"
    if not p.exists():
        print("Error: main.py not found in the current directory.", file=sys.stderr)
        print(
            "Run this command from your project root, or run `moosey-cms init` first.",
            file=sys.stderr,
        )
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
    import questionary

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

    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    # Prompt user for config values
    print("\nLet's configure your Moosey CMS site.\n")

    site_name = questionary.text("Site name:", default="My Site").ask()
    host = questionary.text("Host:", default="0.0.0.0").ask()
    port = questionary.text("Port:", default="8210").ask()
    reload_delay = questionary.text("Reload delay (seconds):", default="0.25").ask()
    admin_prefix = questionary.text("Admin prefix:", default="admin/content").ask()
    admin_templates = questionary.text("Admin templates:", default="admin").ask()

    # Cache configuration
    print("\nCache configuration:\n")
    cache_backend = questionary.select(
        "Cache backend:",
        choices=["memory", "redis"],
        default="memory"
    ).ask()

    cache_ttl = questionary.text(
        "Cache TTL (seconds):",
        default="2592000"
    ).ask()

    redis_url = None
    if cache_backend == "redis":
        redis_url = questionary.text(
            "Redis URL:",
            default="redis://localhost:6379/0"
        ).ask()

    # Generate crypto key
    crypto_key = generate_key()

    # Create config
    config = CMSConfig(
        server=ServerConfig(
            host=host,
            port=int(port),
            reload_delay=float(reload_delay),
        ),
        site=SiteConfig(
            name=site_name,
            admin={"prefix": admin_prefix, "templates": admin_templates},
        ),
        crypto=CryptoConfig(key=crypto_key),
        cache=CacheConfig(
            backend=cache_backend,
            ttl=int(cache_ttl),
            redis_url=redis_url or "redis://localhost:6379/0",
        ),
    )

    # Save config file
    config_path = dst / ".moosey-cms.yaml"
    save_config(config, config_path)
    print(f"\nCreated config: {config_path}")

    # Generate minimal main.py
    main_py = dst / "main.py"
    main_py.write_text(MAIN_PY_TEMPLATE.format(host=host, port=port), encoding="utf-8")
    print(f"Created main.py: {main_py}")

    print(f"\nProject scaffolded to: {dst}")
    print()
    print("Next steps:")
    print(f"  cd {dst.name}")
    print("  moosey-cms dev")
    print()
    print("Visit http://localhost:8210")


MAIN_PY_TEMPLATE = """import uvicorn
from moosey_cms import app

if __name__ == "__main__":
    uvicorn.run(app, host="{host}", port={port})
"""


def cmd_config(args: argparse.Namespace) -> None:
    """Initialize or update config for an existing project."""
    from .lib.config import load_config

    config_path = Path.cwd() / ".moosey-cms.yaml"

    # Check if config exists
    if config_path.exists() and not args.force:
        overwrite = questionary.confirm(
            "Config file already exists. Overwrite?", default=False
        ).ask()
        if not overwrite:
            print("Aborted.")
            return

    # Load existing config to preserve crypto key
    existing = load_config(config_path)

    # Prompt user for config values
    print("\nConfigure your Moosey CMS site.\n")

    site_name = questionary.text("Site name:", default=existing.site.name).ask()
    host = questionary.text("Host:", default=existing.server.host).ask()
    port = questionary.text("Port:", default=str(existing.server.port)).ask()
    reload_delay = questionary.text(
        "Reload delay (seconds):", default=str(existing.server.reload_delay)
    ).ask()
    admin_data = existing.site.admin if isinstance(existing.site.admin, dict) else {"prefix": existing.site.admin.prefix, "templates": existing.site.admin.templates}
    admin_prefix = questionary.text("Admin prefix:", default=admin_data.get("prefix", "admin/content")).ask()
    admin_templates = questionary.text("Admin templates:", default=admin_data.get("templates", "admin")).ask()

    # Cache configuration
    print("\nCache configuration:\n")
    cache_backend = questionary.select(
        "Cache backend:",
        choices=["memory", "redis"],
        default=existing.cache.backend
    ).ask()

    cache_ttl = questionary.text(
        "Cache TTL (seconds):",
        default=str(existing.cache.ttl)
    ).ask()

    redis_url = None
    if cache_backend == "redis":
        redis_url = questionary.text(
            "Redis URL:",
            default=existing.cache.redis_url
        ).ask()

    # Handle crypto key
    if args.generate_key or not existing.crypto.key:
        crypto_key = generate_key()
        print("Generated new crypto key.")
    else:
        crypto_key = existing.crypto.key

    # Create config
    config = CMSConfig(
        server=ServerConfig(
            host=host, port=int(port), reload_delay=float(reload_delay)
        ),
        site=SiteConfig(
            name=site_name,
            admin={"prefix": admin_prefix, "templates": admin_templates},
        ),
        crypto=CryptoConfig(key=crypto_key),
        cache=CacheConfig(
            backend=cache_backend,
            ttl=int(cache_ttl),
            redis_url=redis_url or "redis://localhost:6379/0",
        ),
    )

    # Save config
    save_config(config, config_path)
    print(f"\nSaved config: {config_path}")


def cmd_admin(args: argparse.Namespace) -> None:
    """Copy bundled admin templates and static files into the project."""
    # Copy HTML templates
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

    # Copy static files (optional - for CSS customization)
    static_src = get_bundled_static_dir()
    if static_src.is_dir():
        static_dst = Path(args.static).resolve() / "admin"
        static_dst.mkdir(parents=True, exist_ok=True)

        for f in sorted(static_src.iterdir()):
            if f.is_file():
                shutil.copy2(f, static_dst / f.name)
                print(f"  Created: {static_dst / f.name}")

    print()
    print("Admin installed successfully.")
    print()
    print("Add this config to your init_cms() call:")
    print()
    print('    admin={"prefix": "admin/content", "templates": "admin"}')
    print()
    print("To customize admin colors, edit static/admin/admin.css")
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
    init_p.add_argument(
        "--force", action="store_true", help="Overwrite if directory exists"
    )

    # -- config --
    config_p = sub.add_parser(
        "config", help="Initialize or update config for existing project"
    )
    config_p.add_argument(
        "--force", action="store_true", help="Overwrite existing config"
    )
    config_p.add_argument(
        "--generate-key", action="store_true", help="Force regenerate crypto key"
    )

    # -- admin --
    admin_p = sub.add_parser("admin", help="Copy admin templates and static files")
    admin_p.add_argument(
        "--templates",
        default="./templates",
        help="Path to your project's templates directory (default: ./templates)",
    )
    admin_p.add_argument(
        "--static",
        default="./static",
        help="Path to your project's static directory (default: ./static)",
    )

    # -- dev --
    dev_p = sub.add_parser("dev", help="Run development server (hot-reload)")
    dev_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    dev_p.add_argument(
        "--port", type=int, default=8210, help="Bind port (default: 8210)"
    )

    # -- prod --
    prod_p = sub.add_parser("prod", help="Run production server")
    prod_p.add_argument(
        "--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)"
    )
    prod_p.add_argument(
        "--port", type=int, default=8210, help="Bind port (default: 8210)"
    )

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "config": cmd_config,
        "admin": cmd_admin,
        "dev": cmd_dev,
        "prod": cmd_prod,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
