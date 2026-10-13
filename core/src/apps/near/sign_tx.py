from ubinascii import hexlify

from trezor import wire
from trezor.crypto.curve import ed25519
from trezor.crypto.hashlib import sha256
from trezor.lvglui.scrs import lv
from trezor.messages import NearSignedTx, NearSignTx

from apps.common import paths
from apps.common.keychain import Keychain, auto_keychain

from . import ICON, PRIMARY_COLOR, tokens
from .transaction import Action_Transfer, Transaction


@auto_keychain(__name__)
async def sign_tx(
    ctx: wire.Context, msg: NearSignTx, keychain: Keychain
) -> NearSignedTx:

    await paths.validate_path(ctx, keychain, msg.address_n)
    node = keychain.derive(msg.address_n)
    pubkey = node.public_key()[1:]
    address = hexlify(pubkey).decode()
    ctx.primary_color, ctx.icon_path = lv.color_hex(PRIMARY_COLOR), ICON
    # parse message
    try:
        tx = Transaction.deserialize(msg.raw_tx)
    except BaseException as e:
        raise wire.DataError(f"Invalid message {e}")

    token_action = tx.get_token_transfer_action()
    action = tx.action if len(tx.actions) == 1 else None

    if action is not None and action.action_type == Action_Transfer:
        from trezor.ui.layouts.lvgl import confirm_near_transfer
        from trezor.strings import format_amount

        await confirm_near_transfer(
            ctx,
            tx.signerId,
            tx.receiverId,
            format_amount(action.amount, 24) + " NEAR",
        )
    elif token_action is not None:
        from trezor.strings import format_amount
        from trezor.ui.layouts.lvgl import confirm_near_transfer

        token_info = tokens.token_by_account(tx.receiverId)
        if token_info is not None:
            symbol, decimals = token_info
            amount = f"{format_amount(token_action.token_amount, decimals)} {symbol}"
        else:
            from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

            amount = _(i18n_keys.FORMAT__BASE_UNITS).format(token_action.token_amount)

        await confirm_near_transfer(
            ctx,
            tx.signerId,
            token_action.token_receiver_id,
            amount,
            contract=tx.receiverId,
            method_name=token_action.method_name,
            deposit=format_amount(token_action.deposit, 24) + " NEAR",
            gas=str(token_action.gas),
            unknown_contract=token_info is None,
            deposit_nonzero=token_action.deposit != 0,
            memo=token_action.token_memo,
            msg=token_action.token_msg,
        )
    else:
        from trezor.ui.layouts.lvgl import confirm_blind_sign_common

        await confirm_blind_sign_common(ctx, address, msg.raw_tx)

    signature = ed25519.sign(node.private_key(), sha256(msg.raw_tx).digest())
    from trezor.ui.layouts.lvgl import confirm_final

    await confirm_final(ctx, "NEAR")
    return NearSignedTx(signature=signature)
