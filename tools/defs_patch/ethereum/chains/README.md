# Ethereum Chain Patches

This directory stores local JSON patches for EVM chain definitions that are
missing from, or temporarily ahead of, the current upstream
`common/defs/ethereum/chains/_data/chains` dataset.

## Why this exists

Some generated files in this repository, such as
`core/src/apps/ethereum/networks.py`, are produced from the chain definition
set under `common/defs/ethereum/chains/_data/chains`.

When the upstream chain list has not been updated yet, adding entries directly
to generated files is fragile because the next template generation will
overwrite them. The files in this directory provide a local overlay for that
case.

## How it works

Before `core/tools/build_templates` renders templates, it runs
`tools/apply_eth_chain_patches.py`.

That script copies every `eip155-*.json` file from this directory into:

`common/defs/ethereum/chains/_data/chains`

After the copy step, template generation uses the patched chain set and
produces consistent generated outputs.

## File naming

Use the same filename format as the upstream chain list:

- `eip155-<chainId>.json`

Example:

- `eip155-999.json`
- `eip155-10001.json`

## When to add a file here

Add a patch file here only when:

- the required chain definition is not yet present in the upstream defs
- generated outputs depend on that chain definition
- you want generation and checks to stay reproducible without hand-editing
  generated files

## Maintenance notes

- Prefer removing a local patch once the upstream defs have been updated.
- If an upstream file later appears with the same chain ID, this local patch
  will overwrite it during template generation until the patch is removed.
- Do not edit generated files such as `core/src/apps/ethereum/networks.py`
  directly for these cases; update or add the source JSON patch here instead.
