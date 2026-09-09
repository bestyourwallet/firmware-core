CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
DECODE_MAP = {c: i for i, c in enumerate(CROCKFORD_ALPHABET)}
# Accept ambiguous human-entered characters.
DECODE_MAP.update({"O": 0, "I": 1, "L": 1})
SERIAL_PREFIX = "UKEY"
DEFAULT_WORD_COUNT = 24
PERM_N = DEFAULT_WORD_COUNT
MAX_WORD_COUNT = 24
SERIAL_PAYLOAD_LEN = 16
SERIAL_TOTAL_LEN = 16
SERIAL_GROUP_LEN = 4
# Fixed 80-bit obfuscation constant. This is a public masking layer, not strong cryptographic protection.
OBFUSCATION_KEY = int("5A1CC0DE24BEEFBAD123", 16)


def _validate_word_count(word_count):
    if word_count < 1 or word_count > MAX_WORD_COUNT:
        raise ValueError(f"word count must be between 1 and {MAX_WORD_COUNT}")
    return word_count


def _factorial(n):
    out = 1
    for i in range(2, n + 1):
        out *= i
    return out


def serial_body_length(word_count):
    _validate_word_count(word_count)
    return SERIAL_PAYLOAD_LEN


def _global_rank_from_permutation(perm):
    word_count = len(perm)
    offset = 0
    for n in range(1, word_count):
        offset += _factorial(n)
    return offset + rank_permutation(perm)


def _permutation_from_global_rank(global_rank):
    if global_rank < 0:
        raise ValueError("rank must be >= 0")

    offset = 0
    for n in range(1, MAX_WORD_COUNT + 1):
        size = _factorial(n)
        if global_rank < offset + size:
            return n, unrank_permutation(n, global_rank - offset)
        offset += size
    raise ValueError("rank out of range")


def rank_permutation(perm):
    """
    perm: permutation of 1..n, for example [3, 1, 2, 4, ...]
    Returns a 0-based rank.
    """
    n = _validate_word_count(len(perm))
    pool = list(range(1, n + 1))
    rank = 0
    facts = [1] * (n + 1)
    for i in range(2, n + 1):
        facts[i] = facts[i - 1] * i
    for i, value in enumerate(perm):
        try:
            pos = pool.index(value)
        except ValueError:
            raise ValueError("invalid permutation")
        rank += pos * facts[n - 1 - i]
        pool.pop(pos)
    return rank


def unrank_permutation(n, rank):
    n = _validate_word_count(n)
    if rank < 0:
        raise ValueError("rank must be >= 0")
    facts = [1] * (n + 1)
    for i in range(2, n + 1):
        facts[i] = facts[i - 1] * i
    if rank >= facts[n]:
        raise ValueError("rank out of range")
    pool = list(range(1, n + 1))
    out = []
    remainder = rank
    for i in range(n, 0, -1):
        f = facts[i - 1]
        pos = remainder // f
        remainder %= f
        out.append(pool.pop(pos))
    return out


def _base32_encode_fixed(value, length):
    if value < 0:
        raise ValueError("value must be >= 0")
    chars = [CROCKFORD_ALPHABET[0]] * length
    for i in range(length - 1, -1, -1):
        chars[i] = CROCKFORD_ALPHABET[value & 31]
        value >>= 5
    if value != 0:
        raise ValueError("value too large for fixed body length")
    return "".join(chars)


def _base32_decode(text):
    value = 0
    for ch in text.upper():
        if ch not in DECODE_MAP:
            raise ValueError(f"invalid base32 character: {ch}")
        value = (value << 5) | DECODE_MAP[ch]
    return value


def _format_serial(chars):
    groups = []
    for i in range(0, len(chars), SERIAL_GROUP_LEN):
        groups.append(chars[i : i + SERIAL_GROUP_LEN])
    return SERIAL_PREFIX + "-" + "-".join(groups)


def _parse_serial(serial):
    normalized = serial.strip().upper().replace(" ", "")
    prefix = SERIAL_PREFIX + "-"
    if not normalized.startswith(prefix):
        raise ValueError("serial format invalid")
    payload_text = normalized[len(prefix) :].replace("-", "")
    if len(payload_text) != SERIAL_TOTAL_LEN:
        raise ValueError("serial format invalid")
    return payload_text


def get_serial_word_count(serial):
    payload = _parse_serial(serial)
    obfuscated = _base32_decode(payload)
    global_rank = obfuscated ^ OBFUSCATION_KEY
    word_count, _ = _permutation_from_global_rank(global_rank)
    return word_count


def encode_serial(permutation):
    word_count = _validate_word_count(len(permutation))
    global_rank = _global_rank_from_permutation(permutation)
    obfuscated = global_rank ^ OBFUSCATION_KEY
    return _format_serial(
        _base32_encode_fixed(obfuscated, serial_body_length(word_count))
    )


def decode_serial(serial):
    payload = _parse_serial(serial)
    obfuscated = _base32_decode(payload)
    global_rank = obfuscated ^ OBFUSCATION_KEY
    _, permutation = _permutation_from_global_rank(global_rank)
    return permutation


def reorder_by_permutation(raw_values, permutation):
    """
    Permutation semantics: P[k] means recovered position k takes the P[k]-th
    item from the original list (1-based).
    Example: P = [3, 1, 2] produces [raw[2], raw[0], raw[1]].
    """
    if len(raw_values) != len(permutation):
        raise ValueError("raw_values and permutation length mismatch")
    return [raw_values[pos - 1] for pos in permutation]


def invert_permutation(permutation):
    n = _validate_word_count(len(permutation))
    inverse = [0] * n
    for recovered_position, source_position in enumerate(permutation, start=1):
        if source_position < 1 or source_position > n:
            raise ValueError("invalid permutation")
        inverse[source_position - 1] = recovered_position
    return inverse


def _ti_valid_slots(word_count):
    return tuple(range(1, word_count + 1))


def encode_ti_mnemonic_indexes(
    mnemonic_indexes: list[int], permutation: list[int]
) -> list[int]:
    word_count = _validate_word_count(len(mnemonic_indexes))
    if len(permutation) != PERM_N:
        raise ValueError("TI serial permutation length mismatch")

    raw_24: list[int | None] = [None] * PERM_N
    for index_value, slot in zip(mnemonic_indexes, _ti_valid_slots(word_count)):
        raw_24[slot - 1] = index_value

    encrypted_24 = reorder_by_permutation(raw_24, permutation)
    return [value for value in encrypted_24 if value is not None]


def decode_ti_mnemonic_indexes(
    encrypted_indexes: list[int], permutation: list[int]
) -> list[int]:
    word_count = _validate_word_count(len(encrypted_indexes))
    if len(permutation) != PERM_N:
        raise ValueError("TI serial permutation length mismatch")

    valid_slots = _ti_valid_slots(word_count)
    selected_positions = [source_slot in valid_slots for source_slot in permutation]
    if sum(selected_positions) != word_count:
        raise ValueError("TI serial effective slot count mismatch")

    ordered_24: list[int | None] = [None] * PERM_N
    value_iter = iter(encrypted_indexes)
    for ordered_index, is_effective in enumerate(selected_positions):
        if is_effective:
            ordered_24[ordered_index] = next(value_iter)

    restored_24 = reorder_by_permutation(ordered_24, invert_permutation(permutation))
    restored_indexes = []
    for slot in valid_slots:
        value = restored_24[slot - 1]
        if value is None:
            raise ValueError("TI serial restored mnemonic index missing")
        restored_indexes.append(value)
    return restored_indexes


# SN1 = ""
# SN2 = ""
# MNEMONIC_INDEXES = []
#
# if __name__ == "__main__":
#     for serial in (SN1, SN2):
#         permutation = decode_serial(serial)
#         encrypted_indexes = encode_ti_mnemonic_indexes(MNEMONIC_INDEXES, permutation)
#         restored_indexes = decode_ti_mnemonic_indexes(encrypted_indexes, permutation)
#
#         print(serial)
#         print("encrypted:", encrypted_indexes)
#         print("restored :", restored_indexes)
#         print()
