from common import *

if not utils.BITCOIN_ONLY:
    from apps.sui.helper import INTENT_BYTES
    from apps.sui.transaction import SuiDecodeError, Transaction, _match_sui_transfer


def _uleb(value: int) -> bytes:
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def _u16(value: int) -> bytes:
    return value.to_bytes(2, "little")


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "little")


def _address(byte: int) -> bytes:
    return bytes([byte]) * 32


def _address_str(byte: int) -> str:
    return "0x" + f"{byte:02x}" * 32


def _pure_input(data: bytes) -> bytes:
    return b"\x00" + _uleb(len(data)) + data


def _object_input(byte: int) -> bytes:
    return b"\x01\x00" + _object_ref(byte)


def _arg_gas() -> bytes:
    return b"\x00"


def _arg_input(index: int) -> bytes:
    return b"\x01" + _u16(index)


def _arg_nested_result(command_index: int, result_index: int) -> bytes:
    return b"\x03" + _u16(command_index) + _u16(result_index)


def _object_ref(byte: int) -> bytes:
    return _address(byte) + _u64(1) + _uleb(32) + bytes([byte + 1]) * 32


def _user_standard_sui_transfer() -> bytes:
    return bytes.fromhex(
        "0000000000020008809698000000000000200d7f78a1d41ebfa4ea966d8fbbf4f7b63c990a99c24e084dc7738eb548ac20a6020200010100000101020000010100c1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe0128a7ecbe1291a1b45b24fcc5f63f8972fa5b1698573740fdbb67471214731ecf5df9ba300000000020cf18049334d4d6c2acee33b9dccbad152158f3a831efa037e68c7043857bd8b3c1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe6400000000000000003421000000000000"
    )


def _user_standard_sui_token_transfer() -> bytes:
    return bytes.fromhex(
        "00000000000501008d9aa93ad85e68ec5dd3c99ca6fedd8887e81e8f87a625a1a722bbf54ed5a42659f9ba300000000020c0bd180a28aba02c519292211f1fd239976c01722a489ecfb348aef8e3f10faa0100dc572ce6d0ddecb8e1d776d932bca1d50846ed4f92edfadcf93eafd36da24bc85bf9ba3000000000208619026036df833f6e4993ee875cea3850395e39439afb23beffafab8e7152a00100f2e41ed0f966f012e3f36afeaf1cd6dc3ed60cca2625fd88a1bccfb011b381ca5af9ba300000000020ae3cbd36061c723d056f86fd92ad106a910ddf70f4377d6dc92f4b2121fa0f4c0008102700000000000000200d7f78a1d41ebfa4ea966d8fbbf4f7b63c990a99c24e084dc7738eb548ac20a603030100000201010001020002010000010103000101020100010400c1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe0128a7ecbe1291a1b45b24fcc5f63f8972fa5b1698573740fdbb67471214731ecf5df9ba300000000020cf18049334d4d6c2acee33b9dccbad152158f3a831efa037e68c7043857bd8b3c1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe6400000000000000400d03000000000000"
    )


def _simple_sui_transfer() -> bytes:
    inputs = b"".join(
        [
            _pure_input(_u64(1234567890)),
            _pure_input(_address(0x22)),
        ]
    )
    split_coins = b"\x02" + _arg_gas() + _uleb(1) + _arg_input(0)
    transfer_objects = (
        b"\x01"
        + _uleb(1)
        + _arg_nested_result(0, 0)
        + _arg_input(1)
    )
    ptb = _uleb(2) + inputs + _uleb(2) + split_coins + transfer_objects
    gas_payment = _uleb(1) + _object_ref(0xAA) + _address(0x11) + _u64(1000) + _u64(5000)
    tx_v1 = b"\x00" + ptb + _address(0x11) + gas_payment + b"\x00"
    return INTENT_BYTES + b"\x00" + tx_v1


def _token_transfer_with_hidden_object_transfer() -> bytes:
    inputs = b"".join(
        [
            _pure_input(_u64(1234567890)),
            _pure_input(_address(0x22)),
            _object_input(0x33),
            _object_input(0x44),
            _pure_input(_address(0x55)),
        ]
    )
    split_coins = b"\x02" + _arg_input(2) + _uleb(1) + _arg_input(0)
    displayed_transfer = (
        b"\x01"
        + _uleb(1)
        + _arg_nested_result(0, 0)
        + _arg_input(1)
    )
    hidden_transfer = b"\x01" + _uleb(1) + _arg_input(3) + _arg_input(4)
    ptb = (
        _uleb(5)
        + inputs
        + _uleb(3)
        + split_coins
        + displayed_transfer
        + hidden_transfer
    )
    gas_payment = _uleb(1) + _object_ref(0xAA) + _address(0x11) + _u64(1000) + _u64(5000)
    tx_v1 = b"\x00" + ptb + _address(0x11) + gas_payment + b"\x00"
    return INTENT_BYTES + b"\x00" + tx_v1


def _sui_transfer_with_hidden_object_transfer() -> bytes:
    inputs = b"".join(
        [
            _pure_input(_u64(1234567890)),
            _pure_input(_address(0x22)),
            _object_input(0x33),
            _pure_input(_address(0x44)),
        ]
    )
    split_coins = b"\x02" + _arg_gas() + _uleb(1) + _arg_input(0)
    displayed_transfer = (
        b"\x01"
        + _uleb(1)
        + _arg_nested_result(0, 0)
        + _arg_input(1)
    )
    hidden_transfer = b"\x01" + _uleb(1) + _arg_input(2) + _arg_input(3)
    ptb = (
        _uleb(4)
        + inputs
        + _uleb(3)
        + split_coins
        + displayed_transfer
        + hidden_transfer
    )
    gas_payment = _uleb(1) + _object_ref(0xAA) + _address(0x11) + _u64(1000) + _u64(5000)
    tx_v1 = b"\x00" + ptb + _address(0x11) + gas_payment + b"\x00"
    return INTENT_BYTES + b"\x00" + tx_v1


@unittest.skipUnless(not utils.BITCOIN_ONLY, "altcoin")
class TestSuiTransaction(unittest.TestCase):
    def test_parse_simple_sui_transfer(self):
        tx = Transaction.deserialize(_simple_sui_transfer())
        transfer = _match_sui_transfer(tx.kind)

        self.assertEqual(tx.sender, _address_str(0x11))
        self.assertEqual(tx.gas_payment.owner, _address_str(0x11))
        self.assertEqual(tx.gas_payment.price, 1000)
        self.assertEqual(tx.gas_payment.budget, 5000)
        self.assertEqual(tx.gas_payment.max_fee, "0.000005 SUI")
        self.assertEqual(transfer.recipient, _address_str(0x22))
        self.assertEqual(transfer.amount, "1.23456789 SUI")

    def test_parse_user_standard_sui_transfer(self):
        tx = Transaction.deserialize(_user_standard_sui_transfer())
        transfer = _match_sui_transfer(tx.kind)

        self.assertEqual(
            tx.sender,
            "0xc1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe",
        )
        self.assertEqual(tx.gas_payment.owner, tx.sender)
        self.assertEqual(tx.gas_payment.price, 100)
        self.assertEqual(tx.gas_payment.budget, 2176000)
        self.assertEqual(tx.gas_payment.max_fee, "0.002176 SUI")
        self.assertEqual(
            transfer.recipient,
            "0x0d7f78a1d41ebfa4ea966d8fbbf4f7b63c990a99c24e084dc7738eb548ac20a6",
        )
        self.assertEqual(transfer.amount, "0.01 SUI")

    def test_parse_user_standard_sui_token_transfer(self):
        tx = Transaction.deserialize(_user_standard_sui_token_transfer())
        transfer = _match_sui_transfer(tx.kind)

        self.assertEqual(
            tx.sender,
            "0xc1b8cc2f0632a46a24d300256ce134d5649b7fc3a3d4035b019490e2cee0c9fe",
        )
        self.assertEqual(tx.gas_payment.owner, tx.sender)
        self.assertEqual(tx.gas_payment.price, 100)
        self.assertEqual(tx.gas_payment.budget, 200000)
        self.assertEqual(tx.gas_payment.max_fee, "0.0002 SUI")
        self.assertEqual(
            transfer.recipient,
            "0x0d7f78a1d41ebfa4ea966d8fbbf4f7b63c990a99c24e084dc7738eb548ac20a6",
        )
        self.assertEqual(transfer.amount, "10000 units")
        self.assertEqual(transfer.tx_type, "Token Transfer")
        self.assertEqual(transfer.token, "Unknown Token")

    def test_reject_sui_transfer_with_hidden_object_transfer(self):
        tx = Transaction.deserialize(_sui_transfer_with_hidden_object_transfer())

        self.assertIsNone(_match_sui_transfer(tx.kind))

    def test_reject_token_transfer_with_hidden_object_transfer(self):
        tx = Transaction.deserialize(_token_transfer_with_hidden_object_transfer())

        self.assertIsNone(_match_sui_transfer(tx.kind))

    def test_reject_invalid_intent(self):
        with self.assertRaises(SuiDecodeError):
            Transaction.deserialize(b"\x01\x00\x00")


if __name__ == "__main__":
    unittest.main()
