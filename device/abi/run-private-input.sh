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
