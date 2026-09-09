from common import *

if not utils.BITCOIN_ONLY:
    from apps.aptos.transaction import AptosDecodeError, Transaction, _match_transfer


def _uleb(value: int) -> bytes:
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "little")


def _address(byte: int) -> bytes:
    return bytes([byte]) * 32


def _framework_address() -> bytes:
    return b"\x00" * 31 + b"\x01"


def _address_hex(value: str) -> bytes:
    if value.startswith("0x"):
        value = value[2:]
    return unhexlify(value)




def _bcs_string(value: str) -> bytes:
    data = value.encode()
    return _uleb(len(data)) + data


def _bcs_bytes(value: bytes) -> bytes:
    return _uleb(len(value)) + value


def _bcs_vector(items: list[bytes]) -> bytes:
    return _uleb(len(items)) + b"".join(items)


def _type_tag_aptos_coin() -> bytes:
    return (
        _uleb(7)
        + _framework_address()
        + _bcs_string("aptos_coin")
        + _bcs_string("AptosCoin")
        + _bcs_vector([])
    )


def _entry_payload(
    module: str, function: str, type_args: list[bytes], args: list[bytes]
) -> bytes:
    return (
        _uleb(2)
        + _framework_address()
        + _bcs_string(module)
        + _bcs_string(function)
        + _bcs_vector(type_args)
        + _bcs_vector([_bcs_bytes(arg) for arg in args])
    )


def _raw_tx(payload: bytes) -> bytes:
    return (
        _address(0x11)
        + _u64(7)
        + payload
        + _u64(2000)
        + _u64(100)
        + _u64(1710000000)
        + b"\x04"
    )


@unittest.skipUnless(not utils.BITCOIN_ONLY, "altcoin")
class TestAptosTransaction(unittest.TestCase):
    def test_parse_aptos_account_transfer(self):
        raw_tx = _raw_tx(
            _entry_payload(
                "aptos_account",
                "transfer",
                [],
                [_address(0x22), _u64(123456789)],
            )
        )

        tx = Transaction.deserialize(raw_tx, 0)
        transfer = _match_transfer(tx.payload)

        self.assertEqual(tx.sender, "0x" + "11" * 32)
        self.assertEqual(tx.sequence_number, 7)
        self.assertEqual(tx.max_gas_amount, 2000)
        self.assertEqual(tx.gas_unit_price, 100)
        self.assertEqual(tx.chain_id, 4)
        self.assertEqual(transfer.recipient, "0x" + "22" * 32)
        self.assertEqual(transfer.amount, "1.23456789 APT")
        self.assertEqual(transfer.token, "APT")

    def test_parse_coin_transfer(self):
        raw_tx = _raw_tx(
            _entry_payload(
                "coin",
                "transfer",
                [_type_tag_aptos_coin()],
                [_address(0x33), _u64(100000000)],
            )
        )

        tx = Transaction.deserialize(raw_tx, 0)
        transfer = _match_transfer(tx.payload)

        self.assertEqual(tx.payload.function, "0x1::coin::transfer")
        self.assertEqual(str(tx.payload.type_args[0]), "0x1::aptos_coin::AptosCoin")
        self.assertEqual(transfer.recipient, "0x" + "33" * 32)
        self.assertEqual(transfer.amount, "1 APT")
        self.assertEqual(transfer.token, "0x1::aptos_coin::AptosCoin")

    def test_parse_primary_fungible_store_transfer(self):
        raw_tx = _raw_tx(
            _entry_payload(
                "primary_fungible_store",
                "transfer",
                [],
                [_address(0x44), _address(0x55), _u64(42)],
            )
        )

        tx = Transaction.deserialize(raw_tx, 0)
        transfer = _match_transfer(tx.payload)

        self.assertEqual(transfer.metadata, "0x" + "44" * 32)
        self.assertEqual(transfer.recipient, "0x" + "55" * 32)
        self.assertEqual(transfer.amount, "42 base units")
        self.assertEqual(transfer.token, "Fungible Asset")

    def test_parse_known_fungible_asset_transfer(self):
        raw_tx = _raw_tx(
            _entry_payload(
                "primary_fungible_store",
                "transfer",
                [],
                [
                    _address_hex(
                        "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b"
                    ),
                    _address(0x55),
                    _u64(1234567),
                ],
            )
        )

        tx = Transaction.deserialize(raw_tx, 0)
        transfer = _match_transfer(tx.payload)

        self.assertEqual(
            transfer.metadata,
            "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b",
        )
        self.assertEqual(transfer.recipient, "0x" + "55" * 32)
        self.assertEqual(transfer.amount, "1.234567 USDC")
        self.assertEqual(transfer.token, "USDC")

    def test_parse_fee_payer_transaction(self):
        raw = _raw_tx(
            _entry_payload(
                "aptos_account",
                "transfer",
                [],
                [_address(0x22), _u64(1)],
            )
        )
        raw_with_data = _uleb(1) + raw + _bcs_vector([_address(0x66)]) + _address(0x77)

        tx = Transaction.deserialize(raw_with_data, 1)

        self.assertEqual(tx.secondary_signers, ["0x" + "66" * 32])
        self.assertEqual(tx.fee_payer, "0x" + "77" * 32)

    def test_reject_trailing_data(self):
        raw_tx = _raw_tx(
            _entry_payload(
                "aptos_account",
                "transfer",
                [],
                [_address(0x22), _u64(1)],
            )
        )

        with self.assertRaises(AptosDecodeError):
            Transaction.deserialize(raw_tx + b"\x00", 0)


if __name__ == "__main__":
    unittest.main()
