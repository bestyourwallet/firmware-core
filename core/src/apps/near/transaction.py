from collections import namedtuple

from trezor import wire

import ujson as json

MessageArgs = namedtuple(
    "MessageArgs",
    ["signerId", "publicKey", "nonce", "receiverId", "blockHash", "actions"],
)

# action enum
Action_CreateAccount = 0
Action_DeployContract = 1
Action_FunctionCall = 2
Action_Transfer = 3
Action_Stake = 4
Action_AddKey = 5
Action_DeleteKey = 6
Action_DeleteAccount = 7
# Action_Delegate = 8 # Introduced with NEP-366 to enable meta transactions

MAX_ACTIONS = 100
MAX_TRANSACTION_SIZE = 1_572_864


def _has_duplicate_json_keys(text: str) -> bool:
    # Token arguments have a flat schema. Decode key strings to also detect
    # duplicates written with JSON escapes (e.g. "amount" and "\u0061mount").
    keys: list[str] = []
    offset = 0
    while offset < len(text):
        if text[offset] != '"':
            offset += 1
            continue
        start = offset
        offset += 1
        while offset < len(text) and text[offset] != '"':
            offset += 2 if text[offset] == "\\" else 1
        offset += 1
        end = offset
        while offset < len(text) and text[offset] in " \t\r\n":
            offset += 1
        if offset < len(text) and text[offset] == ":":
            key = json.loads(text[start:end])
            if key in keys:
                return True
            keys.append(key)
    return False


class Action:
    def __init__(self, action_type: int) -> None:
        self.action_type = action_type

    def set_transfer(self, amount: int) -> None:
        self.amount = amount

    def set_function_call(
        self, method_name: str, args: bytes, gas: int, deposit: int
    ) -> None:
        self.method_name = method_name
        self.args = args
        self.gas = gas
        self.deposit = deposit

        if method_name in ("ft_transfer", "ft_transfer_call"):
            try:
                text = args.decode("utf-8")
                payload = json.loads(text)
            except Exception:
                return

            if not isinstance(payload, dict):
                return
            allowed_keys = ("receiver_id", "amount", "memo")
            if method_name == "ft_transfer_call":
                allowed_keys += ("msg",)
            if any(key not in allowed_keys for key in payload):
                return

            receiver_id = payload.get("receiver_id")
            amount = payload.get("amount")
            memo = payload.get("memo")
            msg = payload.get("msg")

            if not isinstance(receiver_id, str) or not 2 <= len(receiver_id) <= 64:
                return
            if not isinstance(amount, str) or not amount or len(amount) > 39:
                return
            if any(c < "0" or c > "9" for c in amount):
                return
            token_amount = int(amount)
            if token_amount >= 1 << 128:
                return
            if memo is not None and not isinstance(memo, str):
                return
            if "msg" in payload and not isinstance(msg, str):
                return
            if _has_duplicate_json_keys(text):
                return

            self.token_receiver_id = receiver_id
            self.token_amount = token_amount
            self.token_memo = memo
            self.token_msg = msg


class Transaction:
    # {
    #     'kind': 'struct',
    #     'fields': [
    #         ['signerId', 'string'],
    #         ['publicKey', PublicKey],
    #         ['nonce', 'u64'],
    #         ['receiverId', 'string'],
    #         ['blockHash', [32]],
    #         ['actions', [Action]],
    #     ],
    # },
    def __init__(self, args: MessageArgs) -> None:
        self.signerId = args.signerId
        self.publicKey = args.publicKey
        self.nonce = args.nonce
        self.receiverId = args.receiverId
        self.blockHash = args.blockHash
        self.actions = args.actions
        self.action = args.actions[0] if args.actions else None

    def get_token_transfer_action(self) -> Action | None:
        if len(self.actions) != 1:
            return None
        action = self.actions[0]
        if (
            action.action_type == Action_FunctionCall
            and getattr(action, "method_name", None)
            in ("ft_transfer", "ft_transfer_call")
            and hasattr(action, "token_receiver_id")
            and hasattr(action, "token_amount")
        ):
            return action
        return None

    @staticmethod
    def deserialize(raw_message: bytes) -> "Transaction":
        if len(raw_message) > MAX_TRANSACTION_SIZE:
            raise wire.DataError("Transaction too large")

        def read_bytes(offset: int, size: int) -> tuple[bytes, int]:
            if size > len(raw_message) - offset:
                raise wire.DataError("Truncated transaction")
            return raw_message[offset : offset + size], offset + size

        def read_u32(offset: int) -> tuple[int, int]:
            data, offset = read_bytes(offset, 4)
            return int.from_bytes(data, "little"), offset

        def read_u64(offset: int) -> tuple[int, int]:
            data, offset = read_bytes(offset, 8)
            return int.from_bytes(data, "little"), offset

        def read_u128(offset: int) -> tuple[int, int]:
            data, offset = read_bytes(offset, 16)
            return int.from_bytes(data, "little"), offset

        def read_string(offset: int) -> tuple[str, int]:
            size, offset = read_u32(offset)
            data, offset = read_bytes(offset, size)
            return data.decode("utf-8"), offset

        def read_byte_array(offset: int) -> tuple[bytes, int]:
            size, offset = read_u32(offset)
            return read_bytes(offset, size)

        def read_public_key(offset: int) -> tuple[bytes, int]:
            key_type, next_offset = read_bytes(offset, 1)
            if key_type[0] == 0:
                size = 32
            elif key_type[0] == 1:
                size = 64
            else:
                raise wire.DataError("Unsupported public key type")
            _, next_offset = read_bytes(next_offset, size)
            return raw_message[offset:next_offset], next_offset

        def read_account_id(offset: int) -> tuple[str, int]:
            size, offset = read_u32(offset)
            if not 2 <= size <= 64:
                raise wire.DataError(
                    "Invalid account ID or unsupported transaction version"
                )
            data, offset = read_bytes(offset, size)
            return data.decode("utf-8"), offset

        def skip_access_key(offset: int) -> int:
            _, offset = read_u64(offset)  # nonce
            permission, offset = read_bytes(offset, 1)
            if permission[0] == 0:
                has_allowance, offset = read_bytes(offset, 1)
                if has_allowance[0] == 1:
                    _, offset = read_u128(offset)
                elif has_allowance[0] != 0:
                    raise wire.DataError("Invalid access key allowance")
                _, offset = read_account_id(offset)  # receiver_id
                methods_len, offset = read_u32(offset)
                if methods_len > (len(raw_message) - offset) // 4:
                    raise wire.DataError("Invalid access key methods length")
                for _ in range(methods_len):
                    _, offset = read_string(offset)
            elif permission[0] != 1:
                raise wire.DataError("Invalid access key permission")
            return offset

        # singer
        signerId, offset = read_account_id(0)
        # publicKey
        publicKey, offset = read_public_key(offset)
        if publicKey[0] != 0:
            raise wire.DataError("Unsupported signing key type")
        # nonce
        nonce, offset = read_u64(offset)
        # receiverId
        receiverId, offset = read_account_id(offset)
        # blockHash
        blockHash, offset = read_bytes(offset, 32)
        # actions_len
        actions_len, offset = read_u32(offset)
        if not 1 <= actions_len <= MAX_ACTIONS:
            raise wire.DataError("Invalid actions count")
        actions = []

        for _ in range(actions_len):
            action_type_raw, offset = read_bytes(offset, 1)
            action_type = action_type_raw[0]

            if action_type not in (
                Action_CreateAccount,
                Action_DeployContract,
                Action_FunctionCall,
                Action_Transfer,
                Action_Stake,
                Action_AddKey,
                Action_DeleteKey,
                Action_DeleteAccount,
            ):
                raise wire.DataError("Invalid action")

            action = Action(action_type)
            if action_type == Action_DeployContract:
                _, offset = read_byte_array(offset)
            elif action_type == Action_FunctionCall:
                method_name, offset = read_string(offset)
                args, offset = read_byte_array(offset)
                gas, offset = read_u64(offset)
                deposit, offset = read_u128(offset)
                action.set_function_call(method_name, args, gas, deposit)
            elif action_type == Action_Transfer:
                amount, offset = read_u128(offset)
                action.set_transfer(amount)
            elif action_type == Action_Stake:
                _, offset = read_u128(offset)
                _, offset = read_public_key(offset)
            elif action_type == Action_AddKey:
                _, offset = read_public_key(offset)
                offset = skip_access_key(offset)
            elif action_type == Action_DeleteKey:
                _, offset = read_public_key(offset)
            elif action_type == Action_DeleteAccount:
                _, offset = read_account_id(offset)
            actions.append(action)

        if offset != len(raw_message):
            raise wire.DataError("Unexpected trailing transaction data")

        return Transaction(
            MessageArgs(
                signerId=signerId,
                publicKey=publicKey,
                nonce=nonce,
                receiverId=receiverId,
                blockHash=blockHash,
                actions=actions,
            )
        )
