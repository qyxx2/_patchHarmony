# PD2307 private ABI input gate

`pd2307-abi.yml` is a `workflow_dispatch`-only GitHub Actions workflow. It does not build or load `droid_lkm.ko`; it only validates the private CRC evidence import path.

## Private bundle

Create the bundle from exactly these paths at its tar root:

```text
symbol-crcs.tsv
module-index.tsv
kheaders.tar.xz
kernel.config
```

Encrypt it with AES-256-CBC and PBKDF2, then store it only in a private GitHub repository or another private immutable location. The corresponding SHA-256 is calculated over the encrypted file.

## Required Fork Secrets

- `PD2307_INPUT_URL`: GitHub Contents API URL for the encrypted bundle.
- `PD2307_INPUT_SHA256`: SHA-256 of that encrypted bundle.
- `PD2307_INPUT_PASSPHRASE`: bundle decryption secret.
- `PD2307_INPUT_TOKEN`: read-only token with access to the private input repository.

The runner checks the SHA-256 before decryption, removes its temporary directory on exit, and uploads only `reports/known-crcs.tsv` plus `reports/input-manifest.json`. Do not print secrets or private paths in commands or logs.

After this workflow has passed, its result demonstrates only that the evidence import is repeatable. It is not a module ABI-compatibility result; genksyms reconstruction and module compilation remain later B1 work.
