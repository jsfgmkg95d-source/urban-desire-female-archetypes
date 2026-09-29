#!/usr/bin/env python3
"""Read-only JSON CLI for local research-preview archetype retrieval."""

import argparse
import json
import sys

sys.dont_write_bytecode = True
from library import InputError, Library, LibraryError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("search", "list"):
        command = commands.add_parser(name)
        command.add_argument("--limit", type=int, default=5 if name == "search" else 30)
        command.add_argument("--tier", choices=("Gold", "Silver") if name == "search" else ("Gold", "Silver", "Reference"))
        command.add_argument("--archetype")
        command.add_argument("--source-category")
        if name == "search":
            command.add_argument("--query", required=True)
        else:
            command.add_argument("--offset", type=int, default=0)
    commands.add_parser("get").add_argument("--id", required=True, dest="card_id")
    commands.add_parser("rules").add_argument("--name", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    try:
        library = Library()
        method = {"search": library.search, "list": library.list, "get": library.get, "rules": library.read_rules}[command]
        result = method(**args)
    except (InputError, LibraryError, OSError) as error:
        print(json.dumps({"quality_status": "research-preview", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
