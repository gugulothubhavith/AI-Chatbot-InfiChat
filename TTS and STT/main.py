from __future__ import annotations

import argparse

from app.cli import run_cli
from app.http_api import run_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Indian Conversational Voice AI Agent")
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="cli",
        help="Run mode: cli or api",
    )
    parser.add_argument("--host", default="0.0.0.0", help="API bind host")
    parser.add_argument("--port", type=int, default=8080, help="API bind port")
    args = parser.parse_args()

    if args.mode == "api":
        run_server(host=args.host, port=args.port)
        return
    run_cli()


if __name__ == "__main__":
    main()
