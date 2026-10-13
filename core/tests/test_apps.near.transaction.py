from common import *

from trezor import wire

if not utils.BITCOIN_ONLY:
    from apps.near.transaction import MAX_ACTIONS, Transaction


def _bytes(data: bytes) -> bytes:
    return len(data).to_bytes(4, "little") + data


def _string(value: str) -> bytes:
    return _bytes(value.encode())


def _transfer(amount: int) -> bytes:
    return b"\x03" + amount.to_bytes(16, "little")


def _call(args: bytes, method="ft_transfer_call", deposit=1) -> bytes:
    return (
        b"\x02"
        + _string(method)
        + _bytes(args)
        + (100_000_000_000_000).to_bytes(8, "little")
        + deposit.to_bytes(16, "little")
    )


def _header(public_key=b"\x00" + b"P" * 32) -> bytes:
    return (
        _string("signer.near")
        + public_key
        + (1).to_bytes(8, "little")
        + _string("usdt.tether-token.near")
        + b"B" * 32
    )


def _tx(actions) -> bytes:
    return _header() + len(actions).to_bytes(4, "little") + b"".join(actions)


@unittest.skipUnless(not utils.BITCOIN_ONLY, "altcoin")
class TestNearTransaction(unittest.TestCase):
    def test_report_deposit_is_preserved(self):
        deposit = 555_555_555_555_555_555_555_555_555
        args = b'{"receiver_id":"victim.near","amount":"1000000"}'
        tx = Transaction.deserialize(_tx([_call(args, deposit=deposit)]))
        action = tx.get_token_transfer_action()
        self.assertIsNotNone(action)
        self.assertEqual(action.token_receiver_id, "victim.near")
        self.assertEqual(action.token_amount, 1000000)
        self.assertEqual(action.deposit, deposit)
        self.assertEqual(action.gas, 100_000_000_000_000)
        self.assertIsNone(action.token_msg)

    def test_call_message_and_memo_are_preserved(self):
        args = b'{"receiver_id":"victim.near","amount":"1","memo":"note","msg":"invest"}'
        action = Transaction.deserialize(_tx([_call(args)])).get_token_transfer_action()
        self.assertEqual(action.token_memo, "note")
        self.assertEqual(action.token_msg, "invest")

    def test_multi_action_never_matches_simple_token_transfer(self):
        call = _call(b'{"receiver_id":"victim.near","amount":"1","msg":""}')
        for actions in ([call, call], [_transfer(1), call], [call, _transfer(1)]):
            tx = Transaction.deserialize(_tx(actions))
            self.assertEqual(len(tx.actions), 2)
            self.assertIsNone(tx.get_token_transfer_action())

    def test_malformed_token_arguments_do_not_match(self):
        args_list = (
            b'[]',
            b'null',
            b'{',
            b'{"receiver_id":"victim.near","amount":1}',
            b'{"receiver_id":"victim.near","amount":"-1"}',
            b'{"receiver_id":"victim.near","amount":"+1"}',
            b'{"receiver_id":"victim.near","amount":"1.0"}',
            b'{"receiver_id":"victim.near","amount":""}',
            b'{"receiver_id":"victim.near","amount":"340282366920938463463374607431768211456"}',
            b'{"receiver_id":"victim.near","amount":"1","msg":{}}',
            b'{"receiver_id":"victim.near","amount":"1","memo":1}',
            b'{"receiver_id":"victim.near","amount":"1","unexpected":"hidden"}',
        )
        for args in args_list:
            tx = Transaction.deserialize(_tx([_call(args)]))
            self.assertIsNone(tx.get_token_transfer_action())

    def test_duplicate_and_escaped_json_keys_do_not_match(self):
        for args in (
            b'{"receiver_id":"victim.near","amount":"1","amount":"100"}',
            b'{"receiver_id":"victim.near","amount":"1","\\u0061mount":"100"}',
            b'{"receiver_id":"victim.near","amount":"1","msg":"a","msg":"b"}',
        ):
            self.assertIsNone(
                Transaction.deserialize(_tx([_call(args)])).get_token_transfer_action()
            )

    def test_key_like_message_text_is_not_a_duplicate(self):
        args = b'{"receiver_id":"victim.near","amount":"1","msg":"\\\"amount\\\":100"}'
        action = Transaction.deserialize(_tx([_call(args)])).get_token_transfer_action()
        self.assertIsNotNone(action)
        self.assertEqual(action.token_msg, '"amount":100')

    def test_u128_token_amount_boundary(self):
        amount = (1 << 128) - 1
        args = ('{"receiver_id":"victim.near","amount":"%s"}' % amount).encode()
        action = Transaction.deserialize(_tx([_call(args)])).get_token_transfer_action()
        self.assertEqual(action.token_amount, amount)

    def test_all_truncated_prefixes_are_rejected(self):
        raw = _tx([_call(b'{"receiver_id":"victim.near","amount":"1","msg":"test"}')])
        for end in range(len(raw)):
            with self.assertRaises((wire.DataError, ValueError)):
                Transaction.deserialize(raw[:end])

    def test_trailing_data_is_rejected(self):
        with self.assertRaises(wire.DataError):
            Transaction.deserialize(_tx([_transfer(1)]) + b"\x00")

    def test_action_count_limits(self):
        for count in (0, MAX_ACTIONS + 1, 0xFFFFFFFF):
            with self.assertRaises(wire.DataError):
                Transaction.deserialize(_header() + count.to_bytes(4, "little"))
        tx = Transaction.deserialize(_tx([_transfer(1)] * MAX_ACTIONS))
        self.assertEqual(len(tx.actions), MAX_ACTIONS)

    def test_unknown_actions_are_rejected(self):
        for tag in (8, 9, 255):
            with self.assertRaises(wire.DataError):
                Transaction.deserialize(_tx([bytes([tag])]))

    def test_unsupported_version_and_signer_key_are_rejected(self):
        with self.assertRaises(wire.DataError):
            Transaction.deserialize(b"\x01" + _tx([_transfer(1)]))
        with self.assertRaises(wire.DataError):
            Transaction.deserialize(_header(b"\x01" + b"P" * 64) + b"\x01\x00\x00\x00" + _transfer(1))
        with self.assertRaises(wire.DataError):
            Transaction.deserialize(_header(b"\x02" + b"P" * 32) + b"\x01\x00\x00\x00" + _transfer(1))

    def test_secp256k1_add_key_preserves_next_action_boundary(self):
        add_key = b"\x05\x01" + b"K" * 64 + b"\x00" * 8 + b"\x01"
        tx = Transaction.deserialize(_tx([add_key, _transfer(42)]))
        self.assertEqual(tx.actions[1].amount, 42)

    def test_invalid_allowance_option_is_rejected(self):
        add_key = (
            b"\x05\x00" + b"K" * 32 + b"\x00" * 8 + b"\x00\x02"
            + _string("victim.near") + b"\x00" * 4
        )
        with self.assertRaises(wire.DataError):
            Transaction.deserialize(_tx([add_key]))


if __name__ == "__main__":
    unittest.main()
