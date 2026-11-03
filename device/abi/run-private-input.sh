#!/usr/bin/env bash
set -euo pipefail

required=(PD2307_INPUT_URL PD2307_INPUT_SHA256 PD2307_INPUT_PASSPHRASE PD2307_INPUT_TOKEN)
for name in "${required[@]}"; do
  [[ -n "${!name:-}" ]] || { echo "missing required secret: $name" >&2; exit 1; }
done

private_dir=$(mktemp -d)
trap 'rm -rf "$private_dir"' EXIT
reports_dir=${REPORTS_DIR:-reports}
mkdir -p "$reports_dir"

curl --fail --silent --show-error --location \
  -H "Accept: application/vnd.github.raw+json" \
  -H "Authorization: Bearer $PD2307_INPUT_TOKEN" \
  "$PD2307_INPUT_URL" -o "$private_dir/input.enc"
printf '%s  %s\n' "$PD2307_INPUT_SHA256" "$private_dir/input.enc" | sha256sum -c -
openssl enc -d -aes-256-cbc -pbkdf2 -pass "pass:$PD2307_INPUT_PASSPHRASE" \
  -in "$private_dir/input.enc" | tar -xzf - -C "$private_dir"

python3 device/abi/extract_crcs.py \
  --symbols "$private_dir/symbol-crcs.tsv" \
  --module-index "$private_dir/module-index.tsv" \
  --vermagic '6.1.145-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64 vivo' \
  --output-dir "$reports_dir"

python3 - "$reports_dir/ddk-diagnostics.json" <<'PY'
import hashlib
import json
import pathlib
import sys

kdir = pathlib.Path("/opt/ddk/kdir/android14-6.1")
tool = kdir / "scripts/genksyms/genksyms"
diagnostics = {
    "schema_version": 1,
    "kdir_exists": kdir.is_dir(),
    "genksyms_exists": tool.is_file(),
    "generated_autoconf_exists": (kdir / "include/generated/autoconf.h").is_file(),
    "generated_utsrelease_exists": (kdir / "include/generated/utsrelease.h").is_file(),
}
if tool.is_file():
    diagnostics["genksyms_sha256"] = hashlib.sha256(tool.read_bytes()).hexdigest()
pathlib.Path(sys.argv[1]).write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n")
PY

/opt/ddk/kdir/android14-6.1/scripts/genksyms/genksyms --help > "$reports_dir/genksyms-usage.txt" 2>&1 || true

printf 'extern void __stack_chk_fail(void);\nEXPORT_SYMBOL(__stack_chk_fail);\n' > "$private_dir/genksyms-probe.c"
/opt/ddk/kdir/android14-6.1/scripts/genksyms/genksyms -D < "$private_dir/genksyms-probe.c" > "$reports_dir/genksyms-probe.txt"
