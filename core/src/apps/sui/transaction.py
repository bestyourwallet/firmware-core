from typing import TYPE_CHECKING
from ubinascii import hexlify

from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.strings import format_amount

from .helper import INTENT_BYTES

if TYPE_CHECKING:
    from trezor.wire import Context


SUI_DECIMALS = 9
SUI_DIGEST_LENGTH = 32


class SuiDecodeError(Exception):
    pass


def _address_to_str(address) -> str:
    return "0x" + hexlify(address).decode()


def _format_sui(amount: int) -> str:
    return format_amount(amount, SUI_DECIMALS) + " SUI"


class BcsReader:
    def __init__(self, data) -> None:
        self.data = data
        self.offset = 0

    def read(self, length: int) -> bytes:
        if length < 0 or self.offset + length > len(self.data):
            raise SuiDecodeError("Unexpected end of transaction")
        value = self.data[self.offset : self.offset + length]
        self.offset += length
        return bytes(value)

    def read_u8(self) -> int:
        return self.read(1)[0]

    def read_bool(self) -> bool:
        value = self.read_u8()
        if value == 0:
            return False
        if value == 1:
            return True
        raise SuiDecodeError("Invalid boolean")

    def read_u16(self) -> int:
        return int.from_bytes(self.read(2), "little")

    def read_u64(self) -> int:
        return int.from_bytes(self.read(8), "little")

    def read_uleb128(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self.read_u8()
            value |= (byte & 0x7F) << shift
            if byte & 0x80 == 0:
                return value
            shift += 7
            if shift > 28:
                raise SuiDecodeError("ULEB128 value is too large")

    def read_bytes(self) -> bytes:
        return self.read(self.read_uleb128())

    def read_address(self) -> str:
        return _address_to_str(self.read(32))

    def ensure_finished(self) -> None:
        if self.offset != len(self.data):
            raise SuiDecodeError("Unexpected trailing transaction data")


class ObjectRef:
    def __init__(self, object_id: str, version: int, digest: bytes) -> None:
        self.object_id = object_id
        self.version = version
        self.digest = digest


class Input:
    def __init__(self, kind: int, value=None) -> None:
        self.kind = kind
        self.value = value


class Argument:
    def __init__(self, kind: int, index: int = 0, sub_index: int = 0) -> None:
        self.kind = kind
        self.index = index
        self.sub_index = sub_index

    def is_gas(self) -> bool:
        return self.kind == 0

    def is_input(self) -> bool:
        return self.kind == 1

    def is_result(self) -> bool:
        return self.kind == 2

    def is_nested_result(self) -> bool:
        return self.kind == 3


class Command:
    def __init__(self, kind: int, data) -> None:
        self.kind = kind
        self.data = data


class SplitCoins:
    def __init__(self, coin: Argument, amounts: list[Argument]) -> None:
        self.coin = coin
        self.amounts = amounts


class MergeCoins:
    def __init__(self, destination: Argument, sources: list[Argument]) -> None:
        self.destination = destination
        self.sources = sources


class TransferObjects:
    def __init__(self, objects: list[Argument], recipient: Argument) -> None:
        self.objects = objects
        self.recipient = recipient


class ProgrammableTransaction:
    def __init__(self, inputs: list[Input], commands: list[Command]) -> None:
        self.inputs = inputs
        self.commands = commands


class GasPayment:
    def __init__(
        self, objects: list[ObjectRef], owner: str, price: int, budget: int
    ) -> None:
        self.objects = objects
        self.owner = owner
        self.price = price
        self.budget = budget

    @property
    def max_fee(self) -> str:
        return _format_sui(self.budget)


class Transaction:
    def __init__(
        self,
        raw_tx: bytes,
        kind,
        sender: str,
        gas_payment: GasPayment,
        expiration,
    ) -> None:
        self.raw_tx = raw_tx
        self.kind = kind
        self.sender = sender
        self.gas_payment = gas_payment
        self.expiration = expiration

    @staticmethod
    def deserialize(raw_tx: bytes) -> "Transaction":
        if raw_tx[:3] != INTENT_BYTES:
            raise SuiDecodeError("Invalid transaction intent")

        reader = BcsReader(raw_tx[3:])
        tx_tag = reader.read_u8()
        if tx_tag != 0:
            raise SuiDecodeError("Unsupported transaction version")

        kind = _read_transaction_kind(reader)
        sender = reader.read_address()
        gas_payment = _read_gas_payment(reader)
        expiration = _read_expiration(reader)
        reader.ensure_finished()
        return Transaction(raw_tx, kind, sender, gas_payment, expiration)

    async def layout(self, ctx: "Context", signer: str) -> None:
        try:
            transfer = _match_sui_transfer(self.kind)
        except SuiDecodeError:
            transfer = None
        if transfer is None:
            from trezor.ui.layouts import confirm_blind_sign_common

            await confirm_blind_sign_common(ctx, signer, self.raw_tx)
            return

        from trezor.ui.layouts import confirm_sui_transfer

        await confirm_sui_transfer(
            ctx,
            sender=self.sender,
            recipient=transfer.recipient,
            amount=transfer.amount,
            max_fee=self.gas_payment.max_fee,
            gas_owner=self.gas_payment.owner,
            gas_price=str(self.gas_payment.price),
            gas_budget=str(self.gas_payment.budget),
            signer=signer,
            tx_type=transfer.tx_type,
            token=transfer.token,
        )


class TransferInfo:
    def __init__(
        self,
        recipient: str,
        amount: str,
        tx_type: str | None = None,
        token: str | None = None,
    ) -> None:
        self.recipient = recipient
        self.amount = amount
        self.tx_type = tx_type
        self.token = token


def _read_transaction_kind(reader: BcsReader):
    kind = reader.read_u8()
    if kind == 0:
        return _read_programmable_transaction(reader)
    raise SuiDecodeError("Unsupported transaction kind")


def _read_programmable_transaction(reader: BcsReader) -> ProgrammableTransaction:
    inputs = []
    for _i in range(reader.read_uleb128()):
        inputs.append(_read_input(reader))

    commands = []
    for _i in range(reader.read_uleb128()):
        commands.append(_read_command(reader))
    return ProgrammableTransaction(inputs, commands)


def _read_input(reader: BcsReader) -> Input:
    kind = reader.read_u8()
    if kind == 0:
        return Input(kind, reader.read_bytes())
    if kind == 1:
        return Input(kind, _read_object_arg(reader))
    if kind == 2:
        object_id = reader.read_address()
        initial_shared_version = reader.read_u64()
        mutable = reader.read_bool()
        return Input(kind, (object_id, initial_shared_version, mutable))
    if kind == 4:
        return Input(kind, _read_object_ref(reader))
    raise SuiDecodeError("Unsupported input kind")


def _read_command(reader: BcsReader) -> Command:
    kind = reader.read_u8()
    if kind == 1:
        objects = _read_argument_vector(reader)
        recipient = _read_argument(reader)
        return Command(kind, TransferObjects(objects, recipient))
    if kind == 2:
        coin = _read_argument(reader)
        amounts = _read_argument_vector(reader)
        return Command(kind, SplitCoins(coin, amounts))
    if kind == 3:
        destination = _read_argument(reader)
        sources = _read_argument_vector(reader)
        return Command(kind, MergeCoins(destination, sources))
    raise SuiDecodeError("Unsupported command kind")


def _read_argument_vector(reader: BcsReader) -> list[Argument]:
    result = []
    for _i in range(reader.read_uleb128()):
        result.append(_read_argument(reader))
    return result


def _read_argument(reader: BcsReader) -> Argument:
    kind = reader.read_u8()
    if kind == 0:
        return Argument(kind)
    if kind in (1, 2):
        return Argument(kind, reader.read_u16())
    if kind == 3:
        return Argument(kind, reader.read_u16(), reader.read_u16())
    raise SuiDecodeError("Unsupported argument kind")


def _read_object_arg(reader: BcsReader):
    kind = reader.read_u8()
    if kind == 0:
        return _read_object_ref(reader)
    if kind == 1:
        object_id = reader.read_address()
        initial_shared_version = reader.read_u64()
        mutable = reader.read_bool()
        return (object_id, initial_shared_version, mutable)
    if kind == 2:
        return _read_object_ref(reader)
    raise SuiDecodeError("Unsupported object argument kind")


def _read_gas_payment(reader: BcsReader) -> GasPayment:
    objects = []
    for _i in range(reader.read_uleb128()):
        objects.append(_read_object_ref(reader))
    owner = reader.read_address()
    price = reader.read_u64()
    budget = reader.read_u64()
    return GasPayment(objects, owner, price, budget)


def _read_object_ref(reader: BcsReader) -> ObjectRef:
    object_id = reader.read_address()
    version = reader.read_u64()
    digest = reader.read_bytes()
    if len(digest) != SUI_DIGEST_LENGTH:
        raise SuiDecodeError("Invalid object digest length")
    return ObjectRef(object_id, version, digest)


def _read_expiration(reader: BcsReader):
    kind = reader.read_u8()
    if kind == 0:
        return None
    if kind == 1:
        return reader.read_u64()
    raise SuiDecodeError("Unsupported transaction expiration")


def _match_sui_transfer(kind):
    if not isinstance(kind, ProgrammableTransaction):
        return None

    transfer = _match_native_sui_transfer(kind)
    if transfer is not None:
        return transfer
    return _match_token_transfer(kind)


def _match_native_sui_transfer(kind: ProgrammableTransaction):
    split_index = None
    split_amount = None
    for index, command in enumerate(kind.commands):
        if command.kind != 2:
            continue
        split = command.data
        if not split.coin.is_gas() or len(split.amounts) != 1:
            continue
        amount = _read_pure_u64(kind, split.amounts[0])
        if amount is None:
            continue
        if split_index is not None:
            raise SuiDecodeError("Multiple SUI transfers")
        split_index = index
        split_amount = amount

    if split_index is None or split_amount is None:
        return None

    matched_commands = [split_index]
    transfer = None
    for index, command in enumerate(kind.commands):
        if command.kind != 1:
            continue
        transfer_objects = command.data
        if len(transfer_objects.objects) != 1:
            continue
        if not _is_split_result(transfer_objects.objects[0], split_index):
            continue
        recipient = _read_pure_address(kind, transfer_objects.recipient)
        if recipient is None:
            continue
        if transfer is not None:
            raise SuiDecodeError("Multiple SUI transfer recipients")
        matched_commands.append(index)
        transfer = TransferInfo(recipient, _format_sui(split_amount))

    if transfer is None:
        return None
    if _has_unmatched_commands(kind, matched_commands):
        return None
    return transfer


def _match_token_transfer(kind: ProgrammableTransaction):
    split_index = None
    split_amount = None
    split_source = None
    for index, command in enumerate(kind.commands):
        if command.kind != 2:
            continue
        split = command.data
        if not split.coin.is_input() or len(split.amounts) != 1:
            continue
        if not _is_object_input(kind, split.coin):
            continue
        amount = _read_pure_u64(kind, split.amounts[0])
        if amount is None:
            continue
        if split_index is not None:
            raise SuiDecodeError("Multiple token transfers")
        split_index = index
        split_amount = amount
        split_source = split.coin

    if split_index is None or split_amount is None or split_source is None:
        return None

    merge_commands = _matching_merge_command_indexes(kind, split_source)
    if merge_commands is None:
        return None

    matched_commands = [split_index]
    matched_commands.extend(merge_commands)
    transfer = None
    for index, command in enumerate(kind.commands):
        if command.kind != 1:
            continue
        transfer_objects = command.data
        if len(transfer_objects.objects) != 1:
            continue
        if not _is_split_result(transfer_objects.objects[0], split_index):
            continue
        recipient = _read_pure_address(kind, transfer_objects.recipient)
        if recipient is None:
            continue
        if transfer is not None:
            raise SuiDecodeError("Multiple token transfer recipients")
        matched_commands.append(index)
        transfer = TransferInfo(
            recipient,
            _(i18n_keys.FORMAT__BASE_UNITS).format(split_amount),
            tx_type=_(i18n_keys.LIST_VALUE__TOKEN_TRANSFER),
            token=_(i18n_keys.LIST_VALUE__UNKNOWN_TOKEN),
        )

    if transfer is None:
        return None
    if _has_unmatched_commands(kind, matched_commands):
        return None
    return transfer


def _matching_merge_command_indexes(
    ptb: ProgrammableTransaction, split_source: Argument
) -> list[int] | None:
    command_indexes = []
    for index, command in enumerate(ptb.commands):
        if command.kind != 3:
            continue
        merge = command.data
        if not _same_argument(merge.destination, split_source):
            continue
        if not merge.sources:
            return None
        for source in merge.sources:
            if not source.is_input() or not _is_object_input(ptb, source):
                return None
        command_indexes.append(index)
        if len(command_indexes) > 1:
            return None
    return command_indexes


def _has_unmatched_commands(
    ptb: ProgrammableTransaction, matched_command_indexes: list[int]
) -> bool:
    for index in range(len(ptb.commands)):
        if index not in matched_command_indexes:
            return True
    return False


def _same_argument(left: Argument, right: Argument) -> bool:
    return (
        left.kind == right.kind
        and left.index == right.index
        and left.sub_index == right.sub_index
    )


def _is_object_input(ptb: ProgrammableTransaction, argument: Argument) -> bool:
    if not argument.is_input() or argument.index >= len(ptb.inputs):
        return False
    return isinstance(ptb.inputs[argument.index].value, ObjectRef)


def _is_split_result(argument: Argument, split_index: int) -> bool:
    if argument.is_nested_result():
        return argument.index == split_index and argument.sub_index == 0
    if argument.is_result():
        return argument.index == split_index
    return False


def _read_pure_u64(ptb: ProgrammableTransaction, argument: Argument):
    data = _read_pure_input(ptb, argument)
    if data is None or len(data) != 8:
        return None
    return int.from_bytes(data, "little")


def _read_pure_address(ptb: ProgrammableTransaction, argument: Argument):
    data = _read_pure_input(ptb, argument)
    if data is None or len(data) != 32:
        return None
    return _address_to_str(data)


def _read_pure_input(ptb: ProgrammableTransaction, argument: Argument):
    if not argument.is_input() or argument.index >= len(ptb.inputs):
        return None
    value = ptb.inputs[argument.index]
    if value.kind != 0:
        return None
    return value.value
