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
                payload = json.loads(args.decode("utf-8"))
            except Exception:
                return

            receiver_id = payload.get("receiver_id")
            amount = payload.get("amount")

            if isinstance(receiver_id, str) and isinstance(amount, str):
                try:
                    self.token_receiver_id = receiver_id
                    self.token_amount = int(amount)
                except ValueError:
                    return


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
        for action in self.actions:
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
        def read_bytes(offset: int, size: int) -> tuple[bytes, int]:
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
            return read_bytes(offset, 33)

        def skip_access_key(offset: int) -> int:
            _, offset = read_u64(offset)  # nonce
            permission, offset = read_bytes(offset, 1)
            if permission[0] == 0:
                has_allowance, offset = read_bytes(offset, 1)
                if has_allowance[0] == 1:
                    _, offset = read_u128(offset)
                _, offset = read_string(offset)  # receiver_id
                methods_len, offset = read_u32(offset)
                for _ in range(methods_len):
                    _, offset = read_string(offset)
            elif permission[0] != 1:
                raise wire.DataError("Invalid access key permission")
            return offset

        # singer
        signerId, offset = read_string(0)
        # publicKey
        publicKey, offset = read_public_key(offset)
        # nonce
        nonce, offset = read_u64(offset)
        # receiverId
        receiverId, offset = read_string(offset)
        # blockHash
        blockHash, offset = read_bytes(offset, 32)
        # actions_len
        actions_len, offset = read_u32(offset)
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
                _, offset = read_string(offset)
            actions.append(action)

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
