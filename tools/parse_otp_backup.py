#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import string
import sys
from pathlib import Path


FLAG_SIZE = 32
OTP_NUM_BLOCKS = 32
OTP_BLOCK_SIZE = 32
FLASH_LOCKED_DATA_SIZE = FLAG_SIZE + OTP_NUM_BLOCKS * OTP_BLOCK_SIZE

BLOCK_NAMES = {
    0: "BATCH",
    1: "BOOTLOADER_VERSION",
    2: "VENDOR_HEADER_LOCK",
    3: "RANDOMNESS",
    7: "BURNIN_TEST",
    8: "ACL16_SESSION_KEY",
    12: "DEVICE_SERIAL",
    13: "FACTORY_TEST",
    14: "RANDOM_KEY",
    15: "CPU_FIRMWARE_INFO",
    16: "ACL16_1_PUBKEY1",
    17: "ACL16_1_PUBKEY2",
    18: "ACL16_2_PUBKEY1",
    19: "ACL16_2_PUBKEY2",
    20: "ACL16_3_PUBKEY1",
    21: "ACL16_3_PUBKEY2",
    22: "ACL16_4_PUBKEY1",
    23: "ACL16_4_PUBKEY2",
    24: "BLE_PUBKEY1",
    25: "BLE_PUBKEY2",
}


def read_backup(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) >= FLASH_LOCKED_DATA_SIZE:
        return raw[:FLASH_LOCKED_DATA_SIZE]

    text = raw.decode("utf-8", errors="ignore")
    hex_bytes = re.findall(r"(?<![0-9a-fA-F])(?:0x)?([0-9a-fA-F]{2})(?![0-9a-fA-F])", text)
    if len(hex_bytes) >= FLASH_LOCKED_DATA_SIZE:
        return bytes(int(byte, 16) for byte in hex_bytes[:FLASH_LOCKED_DATA_SIZE])

    compact_hex = re.sub(r"[^0-9a-fA-F]", "", text)
    if len(compact_hex) >= FLASH_LOCKED_DATA_SIZE * 2:
        return bytes.fromhex(compact_hex[: FLASH_LOCKED_DATA_SIZE * 2])

    raise ValueError(
        f"{path} is too short: need {FLASH_LOCKED_DATA_SIZE} bytes, got {len(raw)} bytes"
    )


def c_string(data: bytes) -> str:
    end = len(data)
    for terminator in (b"\x00", b"\xff"):
        position = data.find(terminator)
        if position != -1:
            end = min(end, position)
    head = data[:end]
    return head.decode("ascii", errors="replace")


def printable_ascii(data: bytes) -> str:
    chars = []
    for byte in data:
        char = chr(byte)
        chars.append(char if char in string.printable and char not in "\r\n\t\x0b\x0c" else ".")
    return "".join(chars)


def status(data: bytes) -> str:
    if all(byte == 0xFF for byte in data):
        return "empty/unlocked"
    if all(byte == 0x00 for byte in data):
        return "zero"
    return "programmed"


def parse_backup(data: bytes) -> dict[str, object]:
    flag = data[:FLAG_SIZE]
    blocks = []
    for index in range(OTP_NUM_BLOCKS):
        start = FLAG_SIZE + index * OTP_BLOCK_SIZE
        block = data[start : start + OTP_BLOCK_SIZE]
        blocks.append(
            {
                "index": index,
                "name": BLOCK_NAMES.get(index, "RESERVED"),
                "status": status(block),
                "hex": block.hex(),
                "ascii": printable_ascii(block),
            }
        )

    summary = {
        "flag": c_string(flag),
        "device_serial": c_string(data[FLAG_SIZE + 12 * OTP_BLOCK_SIZE : FLAG_SIZE + 13 * OTP_BLOCK_SIZE]),
        "cpu_info": c_string(
            data[FLAG_SIZE + 15 * OTP_BLOCK_SIZE : FLAG_SIZE + 15 * OTP_BLOCK_SIZE + OTP_BLOCK_SIZE // 2]
        ),
        "pre_firmware": c_string(
            data[
                FLAG_SIZE + 15 * OTP_BLOCK_SIZE + OTP_BLOCK_SIZE // 2 : FLAG_SIZE
                + 16 * OTP_BLOCK_SIZE
            ]
        ),
        "acl16_pubkeys": {},
        "ble_pubkey": (
            data[FLAG_SIZE + 24 * OTP_BLOCK_SIZE : FLAG_SIZE + 26 * OTP_BLOCK_SIZE].hex()
        ),
    }
    for slot, first_block in enumerate(range(16, 24, 2), start=1):
        start = FLAG_SIZE + first_block * OTP_BLOCK_SIZE
        end = start + OTP_BLOCK_SIZE * 2
        summary["acl16_pubkeys"][str(slot)] = data[start:end].hex()

    return {
        "size": len(data),
        "flag_hex": flag.hex(),
        "flag_ascii": printable_ascii(flag),
        "summary": summary,
        "blocks": blocks,
    }


def print_text(parsed: dict[str, object]) -> None:
    summary = parsed["summary"]
    assert isinstance(summary, dict)

    print(f"FlashLockedData size: {parsed['size']} bytes")
    print(f"flag: {summary['flag']!r}")
    print(f"device_serial: {summary['device_serial']!r}")
    print(f"cpu_info: {summary['cpu_info']!r}")
    print(f"pre_firmware: {summary['pre_firmware']!r}")
    print()
    print("Combined keys:")
    acl16_pubkeys = summary["acl16_pubkeys"]
    assert isinstance(acl16_pubkeys, dict)
    for slot, value in acl16_pubkeys.items():
        print(f"  ACL16 slot {slot}: {value}")
    print(f"  BLE pubkey: {summary['ble_pubkey']}")
    print()
    print("Blocks:")
    print("idx  name                     status          hex")
    print("---  -----------------------  --------------  ----------------------------------------------------------------")
    for block in parsed["blocks"]:
        assert isinstance(block, dict)
        print(
            f"{block['index']:>3}  {block['name']:<23}  {block['status']:<14}  {block['hex']}"
        )
        print(f"     ascii: {block['ascii']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse otp.bin backed up by device_backup_otp()."
    )
    parser.add_argument("input", type=Path, help="otp.bin or a text file containing hex bytes")
    parser.add_argument("--json", action="store_true", help="print parsed data as JSON")
    args = parser.parse_args()

    try:
        parsed = parse_backup(read_backup(args.input))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        print_text(parsed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
