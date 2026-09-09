from typing import TYPE_CHECKING

import trezorproto

decode = trezorproto.decode
encode = trezorproto.encode
encoded_length = trezorproto.encoded_length
type_for_name = trezorproto.type_for_name
type_for_wire = trezorproto.type_for_wire

if TYPE_CHECKING:
    # XXX
    # Note that MessageType "subclasses" are not true subclasses, but instead instances
    # of the built-in metaclass MsgDef. MessageType instances are in fact instances of
    # the built-in type Msg. That is why isinstance checks do not work, and instead the
    # MessageTypeSubclass.is_type_of() method must be used.
    from typing import TypeGuard, TypeVar

    T = TypeVar("T", bound="MessageType")

    class MessageType:
        MESSAGE_NAME: str = "MessageType"
        MESSAGE_WIRE_TYPE: int | None = None

        @classmethod
        def is_type_of(cls: type[T], msg: "MessageType") -> TypeGuard[T]:
            """Identify if the provided message belongs to this type."""
            raise NotImplementedError


def load_message_buffer(
    buffer: bytes,
    msg_wire_type: int,
    experimental_enabled: bool = True,
) -> MessageType:
    msg_type = type_for_wire(msg_wire_type)
    return decode(buffer, msg_type, experimental_enabled)


def dump_message_buffer(msg: MessageType) -> bytearray:
    buffer = bytearray(encoded_length(msg))
    encode(buffer, msg)
    return buffer


def print_message(msg: MessageType, indent: int = 0, drop_none: bool = False):
    if indent == 0:
        print(
            f"========================= BEGIN --- Msg: {msg.MESSAGE_NAME} Type: {msg.MESSAGE_WIRE_TYPE} ========================="
        )

    try:
        for key, value in msg.__dict__.items():
            if value:
                if type(value) is type(msg):
                    print(
                        f"{'    ' * (indent)}{str(key)}:{value.MESSAGE_NAME}:{type(value)} = "
                    )
                    print_message(value, indent + 1)
                else:
                    print(f"{'    ' * (indent)}{str(key)}:{type(value)} = ", end="")
                    if type(value) is not bytes:
                        print(
                            str(value)
                        )  # have to use otherwise may corrupt the output
                    else:
                        print("".join(f"{x:02x}" for x in value))
            elif not drop_none:
                print(f"{'    ' * (indent)}{str(key)}:{type(value)} = {str(value)}")
            else:
                continue

    except Exception as ex:
        from traceback import print_exception

        print(
            f"Error while handling Msg: {msg.MESSAGE_NAME} Type: {msg.MESSAGE_WIRE_TYPE}"
        )
        print_exception(ex)
        pass

    if indent == 0:
        print(
            f"========================= END --- Msg: {msg.MESSAGE_NAME} Type: {msg.MESSAGE_WIRE_TYPE} ========================="
        )


def debug_print_message(
    msg: MessageType,
    indent: int = 0,
    drop_none: bool = False,
    bytes_preview: int = 64,
    bytes_per_line: int = 32,
    full_bytes: bool = False,
):
    if indent == 0:
        print(
            "========================= DEBUG BEGIN --- Msg: "
            + msg.MESSAGE_NAME
            + " Type: "
            + str(msg.MESSAGE_WIRE_TYPE)
            + " ========================="
        )

    try:
        for key, value in msg.__dict__.items():
            prefix = "    " * indent
            key_str = str(key)
            if value:
                if type(value) is type(msg):
                    print(
                        prefix
                        + key_str
                        + ":"
                        + value.MESSAGE_NAME
                        + ":"
                        + str(type(value))
                        + " = "
                    )
                    debug_print_message(
                        value,
                        indent + 1,
                        drop_none=drop_none,
                        bytes_preview=bytes_preview,
                        bytes_per_line=bytes_per_line,
                        full_bytes=full_bytes,
                    )
                elif type(value) is bytes:
                    _debug_print_bytes(
                        key_str,
                        value,
                        indent,
                        bytes_preview,
                        bytes_per_line,
                        full_bytes,
                    )
                else:
                    print(
                        prefix + key_str + ":" + str(type(value)) + " = " + str(value)
                    )
            elif not drop_none:
                print(prefix + key_str + ":" + str(type(value)) + " = " + str(value))
            else:
                continue

    except Exception as ex:
        from traceback import print_exception

        print(
            "Error while debug handling Msg: "
            + msg.MESSAGE_NAME
            + " Type: "
            + str(msg.MESSAGE_WIRE_TYPE)
        )
        print_exception(ex)
        pass

    if indent == 0:
        print(
            "========================= DEBUG END --- Msg: "
            + msg.MESSAGE_NAME
            + " Type: "
            + str(msg.MESSAGE_WIRE_TYPE)
            + " ========================="
        )


def _debug_print_bytes(
    key: str,
    value: bytes,
    indent: int,
    bytes_preview: int,
    bytes_per_line: int,
    full_bytes: bool,
):
    prefix = "    " * indent
    value_len = len(value)
    print(prefix + key + ":" + str(type(value)) + " len=" + str(value_len))

    if value_len == 0:
        return

    if full_bytes:
        line_size = max(1, bytes_per_line)
        for offset in range(0, value_len, line_size):
            end = offset + line_size
            chunk = value[offset:end]
            print(prefix + _bytes_to_hex(chunk))
        return

    preview_len = min(bytes_preview, value_len)
    head = _bytes_to_hex(value[:preview_len])
    print(prefix + key + " head[0:" + str(preview_len) + "] = " + head)

    if value_len > preview_len:
        tail_start = max(value_len - bytes_preview, preview_len)
        tail = _bytes_to_hex(value[tail_start:value_len])
        print(
            prefix
            + key
            + " tail["
            + str(tail_start)
            + ":"
            + str(value_len)
            + "] = "
            + tail
        )


def _bytes_to_hex(value: bytes) -> str:
    return "".join(f"{x:02x}" for x in value)
