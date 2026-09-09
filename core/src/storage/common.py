from micropython import const

from trezor import config, utils

# Namespaces:
# fmt: off
APP_DEVICE             = const(0x01)
APP_RECOVERY           = const(0x02)
APP_RECOVERY_SHARES    = const(0x03)
APP_WEBAUTHN           = const(0x04)
# fmt: on

_FALSE_BYTE = b"\x00"
_TRUE_BYTE = b"\x01"

STORAGE_VERSION_01 = b"\x01"
STORAGE_VERSION_CURRENT = b"\x02"

_RECORD_MAGIC = const(0xA1)
_RECORD_HEADER_SIZE = const(4)
_RECORD_MAX_DATA_LEN = const(255)


def _align4(size: int) -> int:
    return (size + 3) & ~3


def _crc16_update(crc: int, data: bytes | bytearray) -> int:
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _record_crc16(data_len: int, data: bytes | bytearray) -> int:
    crc = _crc16_update(0xFFFF, bytes((_RECORD_MAGIC, data_len)))
    return _crc16_update(crc, data)


def _record_size(key: int) -> int:
    from storage import device

    return device.get_storage_record_size(key)


def _encode_record(data: bytes | bytearray) -> bytearray:
    data_len = len(data)
    if data_len > _RECORD_MAX_DATA_LEN:
        raise ValueError

    padded_data_len = _align4(data_len)
    record = bytearray(_RECORD_HEADER_SIZE + padded_data_len)
    record[0] = _RECORD_MAGIC
    record[1] = data_len
    record[_RECORD_HEADER_SIZE : _RECORD_HEADER_SIZE + data_len] = data
    crc = _record_crc16(
        data_len, record[_RECORD_HEADER_SIZE : _RECORD_HEADER_SIZE + data_len]
    )
    record[2] = (crc >> 8) & 0xFF
    record[3] = crc & 0xFF
    return record


def _decode_record(record: bytes | bytearray) -> bytes | None:
    if len(record) < _RECORD_HEADER_SIZE:
        return None
    if record[0] != _RECORD_MAGIC:
        return None

    data_len = record[1]
    padded_data_len = _align4(data_len)
    record_len = _RECORD_HEADER_SIZE + padded_data_len
    if record_len > len(record):
        return None

    data = record[_RECORD_HEADER_SIZE : _RECORD_HEADER_SIZE + data_len]
    stored_crc = (record[2] << 8) | record[3]
    if stored_crc != _record_crc16(data_len, data):
        return None
    return bytes(data)


def _uses_record_format(app: int) -> bool:
    return utils.USE_ACL16 and app != APP_WEBAUTHN


def set(app: int, key: int, data: bytes, public: bool = False) -> None:
    if _uses_record_format(app):
        config.set(app, key, _encode_record(data), public)
    else:
        config.set(app, key, data, public)


def get(app: int, key: int, public: bool = False) -> bytes | None:
    if _uses_record_format(app):
        raw = config.get(app, key, public, _record_size(key))
        if raw is None:
            return None
        return _decode_record(raw)
    return config.get(app, key, public)


def get_val_len(app: int, key: int, public: bool = False) -> int | None:
    if _uses_record_format(app):
        val = get(app, key, public)
        return None if val is None else len(val)
    return config.get_val_len(app, key, public)


def delete(
    app: int, key: int, public: bool = False, writable_locked: bool = False
) -> None:
    config.delete(app, key, public, writable_locked)


def set_true_or_delete(app: int, key: int, value: bool) -> None:
    if value:
        set_bool(app, key, value)
    else:
        delete(app, key)


def set_bool(app: int, key: int, value: bool, public: bool = False) -> None:
    if value:
        set(app, key, _TRUE_BYTE, public)
    else:
        set(app, key, _FALSE_BYTE, public)


def get_bool(app: int, key: int, public: bool = False) -> bool:
    return get(app, key, public) == _TRUE_BYTE


def set_uint8(app: int, key: int, val: int) -> None:
    set(app, key, val.to_bytes(1, "big"))


def get_uint8(app: int, key: int) -> int | None:
    val = get(app, key)
    if not val:
        return None
    return int.from_bytes(val, "big")


def set_uint16(app: int, key: int, val: int) -> None:
    set(app, key, val.to_bytes(2, "big"))


def get_uint16(app: int, key: int) -> int | None:
    val = get(app, key)
    if not val:
        return None
    return int.from_bytes(val, "big")


def next_counter(app: int, key: int, writable_locked: bool = False) -> int:
    return config.next_counter(app, key, writable_locked)


def set_counter(app: int, key: int, count: int, writable_locked: bool = False) -> None:
    config.set_counter(app, key, count, writable_locked)
