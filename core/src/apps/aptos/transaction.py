from typing import TYPE_CHECKING
from ubinascii import hexlify

from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.strings import format_amount

from . import tokens

if TYPE_CHECKING:
    from trezor.wire import Context


APTOS_DECIMALS = 8
APTOS_COIN = "0x1::aptos_coin::AptosCoin"


class AptosDecodeError(Exception):
    pass


def _address_to_str(address) -> str:
    return "0x" + hexlify(address).decode()


def _is_framework_address(address) -> bool:
    return address[:-1] == b"\x00" * 31 and address[-1] == 1


def _format_apt(amount: int) -> str:
    return format_amount(amount, APTOS_DECIMALS) + " APT"


class BcsReader:
    def __init__(self, data) -> None:
        self.data = data
        self.offset = 0

    def read(self, length: int) -> bytes:
        if length < 0 or self.offset + length > len(self.data):
            raise AptosDecodeError("Unexpected end of transaction")
        value = self.data[self.offset : self.offset + length]
        self.offset += length
        return bytes(value)

    def read_u8(self) -> int:
        return self.read(1)[0]

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
                raise AptosDecodeError("ULEB128 value is too large")

    def read_bytes(self) -> bytes:
        return self.read(self.read_uleb128())

    def read_string(self) -> str:
        try:
            return self.read_bytes().decode()
        except Exception:
            raise AptosDecodeError("Invalid UTF-8 string")

    def read_address(self) -> bytes:
        return self.read(32)

    def ensure_finished(self) -> None:
        if self.offset != len(self.data):
            raise AptosDecodeError("Unexpected trailing transaction data")


class StructTag:
    def __init__(
        self, address: bytes, module: str, name: str, type_params: list["TypeTag"]
    ) -> None:
        self.address = address
        self.module = module
        self.name = name
        self.type_params = type_params

    def __str__(self) -> str:
        result = _short_address(self.address) + "::" + self.module + "::" + self.name
        if self.type_params:
            result += "<" + ", ".join(str(tag) for tag in self.type_params) + ">"
        return result


class TypeTag:
    def __init__(self, variant: int, value=None) -> None:
        self.variant = variant
        self.value = value

    def __str__(self) -> str:
        if self.variant == 0:
            return "bool"
        if self.variant == 1:
            return "u8"
        if self.variant == 2:
            return "u64"
        if self.variant == 3:
            return "u128"
        if self.variant == 4:
            return "address"
        if self.variant == 5:
            return "signer"
        if self.variant == 6:
            return "vector<" + str(self.value) + ">"
        if self.variant == 7 and self.value is not None:
            return str(self.value)
        if self.variant == 8:
            return "u16"
        if self.variant == 9:
            return "u32"
        if self.variant == 10:
            return "u256"
        return "unknown<" + str(self.variant) + ">"


class EntryFunction:
    def __init__(
        self,
        module_address: bytes,
        module_name: str,
        function_name: str,
        type_args: list[TypeTag],
        args: list[bytes],
    ) -> None:
        self.module_address = module_address
        self.module_name = module_name
        self.function_name = function_name
        self.type_args = type_args
        self.args = args

    @property
    def function(self) -> str:
        return (
            _short_address(self.module_address)
            + "::"
            + self.module_name
            + "::"
            + self.function_name
        )


class Transaction:
    def __init__(
        self,
        raw_tx: bytes,
        sender: str,
        sequence_number: int,
        payload,
        max_gas_amount: int,
        gas_unit_price: int,
        expiration_timestamp_secs: int,
        chain_id: int,
        secondary_signers=None,
        fee_payer=None,
    ) -> None:
        self.raw_tx = raw_tx
        self.sender = sender
        self.sequence_number = sequence_number
        self.payload = payload
        self.max_gas_amount = max_gas_amount
        self.gas_unit_price = gas_unit_price
        self.expiration_timestamp_secs = expiration_timestamp_secs
        self.chain_id = chain_id
        self.secondary_signers = secondary_signers or []
        self.fee_payer = fee_payer

    @staticmethod
    def deserialize(raw_tx: bytes, tx_type: int) -> "Transaction":
        reader = BcsReader(raw_tx)
        if tx_type == 0:
            tx = _read_raw_transaction(reader, raw_tx)
        elif tx_type == 1:
            tx = _read_raw_transaction_with_data(reader, raw_tx)
        else:
            raise AptosDecodeError("Invalid transaction type")
        reader.ensure_finished()
        return tx

    async def layout(self, ctx: "Context", signer: str) -> None:
        try:
            transfer = _match_transfer(self.payload)
        except AptosDecodeError:
            transfer = None
        if transfer is None:
            from trezor.ui.layouts import confirm_blind_sign_common

            await confirm_blind_sign_common(ctx, signer, self.raw_tx)
            return

        from trezor.ui.layouts import confirm_aptos_transfer

        await confirm_aptos_transfer(
            ctx,
            sender=self.sender,
            recipient=transfer.recipient,
            amount=transfer.amount,
            max_fee=_format_apt(self.max_gas_amount * self.gas_unit_price),
            function=self.payload.function if self.payload else "",
            chain_id=str(self.chain_id),
            token=transfer.token,
            signer=signer,
            metadata=transfer.metadata,
            fee_payer=self.fee_payer,
            secondary_signers=", ".join(self.secondary_signers)
            if self.secondary_signers
            else None,
        )


class TransferInfo:
    def __init__(self, recipient: str, amount: str, token: str, metadata=None) -> None:
        self.recipient = recipient
        self.amount = amount
        self.token = token
        self.metadata = metadata


def _short_address(address) -> str:
    if _is_framework_address(address):
        return "0x1"
    return _address_to_str(address)


def _read_raw_transaction(reader: BcsReader, raw_tx: bytes) -> Transaction:
    sender = _address_to_str(reader.read_address())
    sequence_number = reader.read_u64()
    payload = _read_payload(reader)
    max_gas_amount = reader.read_u64()
    gas_unit_price = reader.read_u64()
    expiration_timestamp_secs = reader.read_u64()
    chain_id = reader.read_u8()
    return Transaction(
        raw_tx,
        sender,
        sequence_number,
        payload,
        max_gas_amount,
        gas_unit_price,
        expiration_timestamp_secs,
        chain_id,
    )


def _read_raw_transaction_with_data(reader: BcsReader, raw_tx: bytes) -> Transaction:
    variant = reader.read_uleb128()
    tx = _read_raw_transaction(reader, raw_tx)
    tx.secondary_signers = [
        _address_to_str(reader.read_address()) for _ in _range(reader)
    ]
    if variant == 0:
        return tx
    if variant == 1:
        tx.fee_payer = _address_to_str(reader.read_address())
        return tx
    raise AptosDecodeError("Unknown RawTransactionWithData variant")


def _read_payload(reader: BcsReader):
    variant = reader.read_uleb128()
    if variant == 2:
        return _read_entry_function(reader)
    # Keep unknown payloads on the existing blind-sign path.
    raise AptosDecodeError("Unsupported transaction payload")


def _read_entry_function(reader: BcsReader) -> EntryFunction:
    module_address = reader.read_address()
    module_name = reader.read_string()
    function_name = reader.read_string()
    type_args = [_read_type_tag(reader) for _ in _range(reader)]
    args = [reader.read_bytes() for _ in _range(reader)]
    return EntryFunction(module_address, module_name, function_name, type_args, args)


def _read_type_tag(reader: BcsReader) -> TypeTag:
    variant = reader.read_uleb128()
    if variant == 6:
        return TypeTag(variant, _read_type_tag(reader))
    if variant == 7:
        address = reader.read_address()
        module = reader.read_string()
        name = reader.read_string()
        type_params = [_read_type_tag(reader) for _ in _range(reader)]
        return TypeTag(variant, StructTag(address, module, name, type_params))
    return TypeTag(variant)


def _range(reader: BcsReader) -> range:
    return range(reader.read_uleb128())


def _match_transfer(payload):
    if payload is None or not _is_framework_address(payload.module_address):
        return None

    module = payload.module_name
    function = payload.function_name
    args = payload.args

    if module == "aptos_account" and function == "transfer" and len(args) >= 2:
        recipient = _read_arg_address(args[0])
        amount = _read_arg_u64(args[1])
        return TransferInfo(recipient, _format_apt(amount), "APT")

    if (
        module in ("coin", "aptos_account")
        and function in ("transfer", "transfer_coins")
        and payload.type_args
        and len(args) >= 2
    ):
        token = str(payload.type_args[0])
        recipient = _read_arg_address(args[0])
        amount = _read_arg_u64(args[1])
        return TransferInfo(recipient, _format_coin_amount(amount, token), token)

    if module == "primary_fungible_store" and function == "transfer" and len(args) >= 3:
        metadata = _read_arg_address(args[0])
        recipient = _read_arg_address(args[1])
        amount = _read_arg_u64(args[2])
        token_info = tokens.token_by_metadata(metadata)
        if token_info is not None:
            amount_str = (
                format_amount(amount, token_info.decimals) + " " + token_info.symbol
            )
            token = token_info.symbol
        else:
            amount_str = _(i18n_keys.FORMAT__BASE_UNITS).format(amount)
            token = (
                str(payload.type_args[0])
                if payload.type_args
                else _(i18n_keys.LIST_VALUE__FUNGIBLE_ASSET)
            )
        return TransferInfo(
            recipient,
            amount_str,
            token,
            metadata=metadata,
        )

    return None


def _read_arg_address(arg: bytes) -> str:
    if len(arg) != 32:
        raise AptosDecodeError("Invalid address argument")
    return _address_to_str(arg)


def _read_arg_u64(arg: bytes) -> int:
    if len(arg) != 8:
        raise AptosDecodeError("Invalid u64 argument")
    return int.from_bytes(arg, "little")


def _format_coin_amount(amount: int, token: str) -> str:
    if token == APTOS_COIN:
        return _format_apt(amount)
    return _(i18n_keys.FORMAT__BASE_UNITS).format(amount)
