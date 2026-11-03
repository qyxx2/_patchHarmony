#!/usr/bin/env python3
"""Extract a deterministic, target-vermagic CRC evidence set."""

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

SYMBOL_HEADER = ["symbol", "crc", "source_module"]
MODULE_HEADER = ["module_path", "vermagic", "version_record_count", "has_nonempty___versions"]


def read_rows(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != expected_header:
            raise ValueError(f"invalid header in {path.name}: expected {expected_header}")
        rows = list(reader)
    if any(None in row.values() for row in rows):
        raise ValueError(f"invalid row width in {path.name}")
    return rows


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--module-index", required=True, type=Path)
    parser.add_argument("--vermagic", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        modules = read_rows(args.module_index, MODULE_HEADER)
        symbols = read_rows(args.symbols, SYMBOL_HEADER)
        targets = {row["module_path"] for row in modules if row["vermagic"].strip() == args.vermagic}
        if not targets:
            raise ValueError("no target modules for requested vermagic")
        selected = [row for row in symbols if row["source_module"] in targets]
        by_symbol: dict[str, set[str]] = {}
        for row in selected:
            by_symbol.setdefault(row["symbol"], set()).add(row["crc"])
        conflicts = sorted(symbol for symbol, crcs in by_symbol.items() if len(crcs) != 1)
        if conflicts:
            raise ValueError(f"conflicting CRC for symbols: {', '.join(conflicts)}")
        output_rows = [(symbol, next(iter(by_symbol[symbol]))) for symbol in sorted(by_symbol)]
        parent = args.output_dir.parent
        with tempfile.TemporaryDirectory(dir=parent, prefix=".crc-output-") as temporary:
            temp_output = Path(temporary) / "output"
            temp_output.mkdir()
            with (temp_output / "known-crcs.tsv").open("w", newline="", encoding="utf-8") as target:
                writer = csv.writer(target, delimiter="\t", lineterminator="\n")
                writer.writerow(["symbol", "crc"])
                writer.writerows(output_rows)
            manifest = {"schema_version": 1, "target_vermagic": args.vermagic, "module_count": len(targets), "selected_record_count": len(selected), "unique_symbol_count": len(output_rows), "symbols_sha256": digest(args.symbols), "module_index_sha256": digest(args.module_index)}
            (temp_output / "input-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.output_dir.exists():
                shutil.rmtree(args.output_dir)
            os.replace(temp_output, args.output_dir)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
