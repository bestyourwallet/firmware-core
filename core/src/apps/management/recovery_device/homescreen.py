import storage
import storage.device as storage_device
import storage.recovery as storage_recovery
from trezor import utils, wire
from trezor.crypto.hashlib import sha256
from trezor.enums import BackupType, MessageType
from trezor.errors import MnemonicError
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs import theme_path_png
from trezor.messages import Success
from trezor.ui.layouts import show_popup, show_success, show_ukey_app_guide
from trezor.ui.layouts.lvgl.recovery import request_word

from apps.base import set_homescreen
from apps.common import backup_types, mnemonic

from . import layout, recover

# from apps.homescreen.homescreen import homescreen


# async def recovery_homescreen() -> None:
#     if not storage_recovery.is_in_progress():
#         workflow.set_default(homescreen)
#         return

#     # recovery process does not communicate on the wire
#     ctx = wire.DUMMY_CONTEXT
#     await recovery_process(ctx)


async def recovery_process(ctx: wire.GenericContext, type: str = "phrase") -> Success:
    wire.AVOID_RESTARTING_FOR = (
        MessageType.Initialize,
        MessageType.GetFeatures,
        MessageType.EndSession,
    )
    try:
        if type == "phrase":
            return await _continue_recovery_process(ctx)
        elif type in ("lite", "ring"):
            utils.set_backup_lite() if type == "lite" else utils.set_backup_ring()
            return await _continue_recovery_process_lite(ctx)
        elif type == "ti":
            utils.set_backup_seed_ti()
            return await _continue_recovery_process_ti(ctx)
        else:
            raise wire.ProcessError(f"Unsupported recovery type: {type}")

    except recover.RecoveryAborted:
        dry_run = storage_recovery.is_dry_run()
        if dry_run:
            storage_recovery.end_progress()
        else:
            await show_popup(_(i18n_keys.TITLE__PLEASE_WAIT))
            storage.wipe()
        raise wire.ActionCancelled
    except Exception:
        raise wire.ProcessError("Recovery process failed")


async def _continue_recovery_process_ti(
    ctx: wire.GenericContext,
) -> Success:
    from apps.management import serial_codec
    from trezor.lvglui.scrs.common import FullSizeWindow
    from trezor.lvglui.scrs.recovery_device import SerialProtection
    from trezor.lvglui.scrs.pinscreen import InputTiSerial, InputTiCodeConfirm
    from trezor.crypto import bip39

    # Import confirm_exit_backup_process from the same location as backup_with_seed_ti
    from trezor.ui.layouts.lvgl import confirm_exit_backup_process

    dry_run = storage_recovery.is_dry_run()
    word_count = await _request_word_count(ctx, dry_run, allowed_counts=(12, 18, 24))
    await _request_share_first_screen(ctx, word_count)

    while True:
        background_screen = FullSizeWindow(None, None)
        try:
            ask_screen = SerialProtection()
            ask_result = await ctx.wait(ask_screen.request())

            if ask_result == 0:  # Cancel/Skip option
                if await confirm_exit_backup_process(ctx):
                    break
                continue

            serial = ""
            permutation = None
            if ask_result == 1:  # Confirm/Use protection option
                while True:
                    screen = InputTiSerial()
                    serial_input = await ctx.wait(screen.request())
                    if not serial_input:
                        if await confirm_exit_backup_process(ctx):
                            break
                        continue

                    serial = str(serial_input)
                    try:
                        permutation = serial_codec.decode_serial(serial)
                        if len(permutation) != serial_codec.PERM_N:
                            raise ValueError("serial permutation length mismatch")
                    except ValueError as exc:
                        if __debug__:
                            print(
                                "_continue_recovery_process_ti serial validation failed:",
                                exc,
                            )
                        await layout.show_ti_confirmation_failure(ctx)
                        continue
                    break

                if not serial:
                    break

            numbers: list[int] = []
            for i in range(word_count):
                while True:
                    ti_confirm = InputTiCodeConfirm(None, i + 1)
                    data = await ctx.wait(ti_confirm.request())

                    if data == 0:
                        if await confirm_exit_backup_process(ctx):
                            break
                        continue

                    numbers.append(int(data))
                    break

                if len(numbers) != i + 1:
                    break

            if len(numbers) != word_count:
                break

            decoded_numbers = numbers
            if permutation is not None:
                decoded_numbers = serial_codec.decode_ti_mnemonic_indexes(
                    numbers, permutation
                )

            words_list = []
            for num in decoded_numbers:
                if num < 0:
                    raise ValueError("mnemonic word index out of range")
                words_list.append(bip39.get_word(num))

            words = " ".join(words_list)
            secret = recover.process_bip39(words=words)
            backup_type = BackupType.Bip39
        except (MnemonicError, ValueError, IndexError) as exc:
            if __debug__:
                print(f"Error processing TI mnemonic: {exc}")
            await layout.show_ti_confirmation_failure(ctx)
            continue
        finally:
            background_screen.destroy(100)

        if dry_run:
            return await _finish_recovery_dry_run(ctx, secret, backup_type)
        return await _finish_recovery(ctx, secret, backup_type)

    # If we reach here, the process was cancelled
    raise wire.ActionCancelled


async def _continue_recovery_process_lite(
    ctx: wire.GenericContext,
) -> Success:

    from trezor.ui.layouts.lvgl.lite import backup_with_lite_import

    words_length = 0

    secret = await backup_with_lite_import(ctx)

    if secret == 0:
        raise RuntimeError("secret is zero")
    if isinstance(secret, str):
        words_length = len(secret.split())

    is_slip39 = backup_types.is_slip39_word_count(words_length)

    if is_slip39:
        secret, share = recover.process_slip39(words=str(secret))
    else:
        secret = recover.process_bip39(words=str(secret))
        share = None

    if is_slip39 and share is None:
        raise RuntimeError("SLIP-39 share should not be None")

    backup_type = backup_types.infer_backup_type(is_slip39, share)

    if secret is None:
        raise ValueError("Secret cannot be None")
    result = await _finish_recovery(ctx, secret, backup_type)

    return result


async def _continue_recovery_process(
    ctx: wire.GenericContext,
) -> Success:
    # gather the current recovery state from storage
    dry_run = storage_recovery.is_dry_run()
    word_count, backup_type = None, None  # recover.load_slip39_state()

    # Both word_count and backup_type are derived from the same data. Both will be
    # either set or unset. We use 'backup_type is None' to detect status of both.
    # The following variable indicates that we are (re)starting the first recovery step,
    # which includes word count selection.
    is_first_step = backup_type is None

    if not is_first_step:
        assert word_count is not None
        # If we continue recovery, show starting screen with word count immediately.
        await _request_share_first_screen(ctx, word_count)

    secret = None
    words = None
    while secret is None:
        mods = utils.unimport_begin()
        if not words:
            if is_first_step:
                # If we are starting recovery, ask for word count first...
                if not word_count:
                    word_count = await _request_word_count(
                        ctx, dry_run, allowed_counts=(12, 18, 24)
                    )
                    # from apps.common import backup_types

                    # if backup_types.is_slip39_word_count(word_count):
                    #     word_count = 12
                # ...and only then show the starting screen with word count.
                await _request_share_first_screen(ctx, word_count)
            assert word_count is not None

            # ask for mnemonic words one by one
            try:
                words = await layout.request_mnemonic(ctx, word_count, backup_type)
            except wire.ActionCancelled:
                if not is_first_step:
                    try:
                        await layout.confirm_abort(ctx, dry_run)
                    except wire.ActionCancelled:
                        pass
                    else:
                        raise recover.RecoveryAborted
                continue

            # if they were invalid or some checks failed we continue and request them again
            if not words:
                continue

        try:
            secret, backup_type = await _process_words(ctx, words)
            is_first_step = False
            if secret is None:
                # if the secret is None, we assume the backup_type is SLIP-39
                # and we need to ask for the next share
                words = None
                utils.unimport_end(mods)
                continue
            # If _process_words succeeded, we now have both backup_type (from
            # its result) and word_count (from _request_word_count earlier), which means
            # that the first step is complete.
        except MnemonicError:
            assert words is not None
            words_list = words.split(" ")
            while True:
                result = await layout.show_invalid_mnemonic(ctx, words_list)
                if result is not None:
                    assert word_count is not None
                    try:
                        word = await request_word(
                            ctx,
                            result,
                            word_count,
                            is_slip39=backup_types.is_slip39_word_count(word_count),
                        )
                    except wire.ActionCancelled:
                        continue
                    else:
                        words_list[result] = word
                        words = " ".join(words_list)
                        break
                else:
                    words = None
                    break
        # except BaseException as e:
        #     import sys

        #     sys.print_exception(e)
    assert backup_type is not None
    if dry_run:
        result = await _finish_recovery_dry_run(ctx, secret, backup_type)
    else:
        result = await _finish_recovery(ctx, secret, backup_type)

    return result


async def _finish_recovery_dry_run(
    ctx: wire.GenericContext, secret: bytes, backup_type: BackupType
) -> Success:
    if backup_type is None:
        raise RuntimeError

    is_slip39 = backup_types.is_slip39_backup_type(backup_type)

    if utils.USE_ACL16_WALLET_CRYPTO:
        from trezor.crypto import se_acl16

        result = se_acl16.check(secret)
    else:
        digest_input = sha256(secret).digest()
        stored = mnemonic.get_secret()
        digest_stored = sha256(stored).digest()
        result = utils.consteq(digest_stored, digest_input)
    # Check that the identifier, extendable backup flag and iteration exponent match as well
    if is_slip39:
        if not backup_types.is_extendable_backup_type(backup_type):
            result &= (
                storage_device.get_slip39_identifier()
                == storage_recovery.get_slip39_identifier()
            )
        result &= backup_types.is_extendable_backup_type(
            storage_device.get_backup_type()
        ) == backup_types.is_extendable_backup_type(backup_type)
        result &= (
            storage_device.get_slip39_iteration_exponent()
            == storage_recovery.get_slip39_iteration_exponent()
        )

    storage_recovery.end_progress()

    await layout.show_dry_run_result(ctx, result, is_slip39, secret)

    if result:
        return Success(message="The seed is valid and matches the one in the device")
    else:
        raise wire.ProcessError("The seed does not match the one in the device")


async def _finish_recovery(
    ctx: wire.GenericContext, secret: bytes, backup_type: BackupType
) -> Success:
    if backup_type is None:
        raise RuntimeError
    identifier = None
    exponent = None
    # storage_device.set_backup_type(backup_type)
    if backup_types.is_slip39_backup_type(backup_type):
        if not backup_types.is_extendable_backup_type(backup_type):
            identifier = storage_recovery.get_slip39_identifier()
            if identifier is None:
                # The identifier needs to be stored in storage at this point
                raise RuntimeError
            storage_device.set_slip39_identifier(identifier)

        exponent = storage_recovery.get_slip39_iteration_exponent()
        if exponent is None:
            # The iteration exponent needs to be stored in storage at this point
            raise RuntimeError
        storage_device.set_slip39_iteration_exponent(exponent)
    storage_device.store_mnemonic_secret(
        secret,
        backup_type,
        needs_backup=False,
        no_backup=False,
        identifier=identifier,
        iteration_exponent=exponent,
    )
    storage_recovery.end_progress()
    if __debug__:
        print("Recovery process finished, secret stored.")
    await show_success(
        ctx,
        "success_recovery",
        _(i18n_keys.SUBTITLE__DEVICE_RECOVER_WALLET_IS_READY),
        header=_(i18n_keys.TITLE__WALLET_IS_IMPORT_READY),
        button=_(i18n_keys.BUTTON__CONTINUE),
        icon=theme_path_png("hidden-wallet"),
        nav_back=False,
    )
    # ask user to open air-gapped mode
    # await enable_airgap_mode()
    from trezor.lvglui.scrs import get_default_wallpaper

    storage_device.set_homescreen(get_default_wallpaper())
    if False:  # isinstance(ctx, wire.DummyContext):
        utils.make_show_app_guide()
    else:
        await show_ukey_app_guide()
        set_homescreen()
    return Success(message="Device recovered")


async def _request_word_count(
    ctx: wire.GenericContext,
    dry_run: bool,
    allowed_counts: tuple[int, ...] | None = None,
) -> int:
    # await layout.homescreen_dialog(
    #     ctx, _(i18n_keys.BUTTON__CONTINUE), _(i18n_keys.TITLE__SELECT_NUMBER_OF_WORDS)
    # )

    # ask for the number of words
    return await layout.request_word_count(ctx, dry_run, allowed_counts)


async def _process_words(
    ctx: wire.GenericContext, words: str
) -> tuple[bytes | None, BackupType]:
    word_count = len(words.split(" "))
    is_slip39 = backup_types.is_slip39_word_count(word_count)

    share = None
    if not is_slip39:  # BIP-39
        secret: bytes | None = recover.process_bip39(words)
    else:
        secret, share = recover.process_slip39(words)

    backup_type = backup_types.infer_backup_type(is_slip39, share)
    if __debug__:
        print(f"secret: {secret}, backup_type: {backup_type}")
    if secret is None:  # SLIP-39
        assert share is not None
        if share.group_count and share.group_count > 1:
            if __debug__:
                print(
                    f"share.index: {share.index}, share.group_index: {share.group_index}"
                )
            # await layout.show_group_share_success(ctx, share.index, share.group_index)
            await layout.show_success(
                ctx,
                "Enter share",
                header=_(
                    i18n_keys.TITLE__YOU_HAVE_ENTERED_SHARE_STR_FROM_GROUP_STR
                ).format(num1=share.index + 1, num2=share.group_index + 1),
                content=_(
                    i18n_keys.TITLE__YOU_HAVE_ENTERED_SHARE_STR_FROM_GROUP_STR_DESC
                ),
                button=_(i18n_keys.BUTTON__CONTINUE),
            )
        if __debug__:
            print(f"share.threshold: {share.threshold}")
        await _request_share_next_screen(ctx, share.threshold, share.group_index)

    return secret, backup_type


async def _request_share_first_screen(
    ctx: wire.GenericContext, word_count: int
) -> None:
    if backup_types.is_slip39_word_count(word_count):
        # remaining = storage_recovery.fetch_slip39_remaining_shares()
        # if remaining:
        #     await _request_share_next_screen(ctx, 0)
        # else:
        # TODO: should use a different style for SLIP-39 ?
        btn_text = _(i18n_keys.BUTTON__CONTINUE)
        title = _(i18n_keys.TITLE__ENTER_RECOVERY_PHRASE)
        await layout.homescreen_dialog(ctx, btn_text, title, f"({word_count} words)")
    else:  # BIP-39
        btn_text = _(i18n_keys.BUTTON__CONTINUE)
        title = _(i18n_keys.TITLE__ENTER_RECOVERY_PHRASE)
        await layout.homescreen_dialog(ctx, btn_text, title, f"({word_count} words)")


async def _request_share_next_screen(
    ctx: wire.GenericContext, threshold: int, group_index: int
) -> None:
    remaining = storage_recovery.fetch_slip39_remaining_shares()
    group_count = storage_recovery.get_slip39_group_count()
    if not remaining:
        # 'remaining' should be stored at this point
        raise RuntimeError
    if __debug__:
        print(f"remaining: {remaining}, group_count: {group_count}")
    # if group_count > 1:
    #     await layout.homescreen_dialog(
    #         ctx,
    #         "Enter",
    #         "More shares needed",
    #         info_func=_show_remaining_groups_and_shares,
    #     )
    # else:
    # text = strings.format_plural("{count} more {plural}", remaining[0], "share")
    # await layout.homescreen_dialog(ctx, "Enter share", text, "needed to enter")
    if __debug__:
        print(f"threshold: {threshold}, remaining: {remaining[group_index]}")
    if remaining[group_index] > 0:
        await layout.show_success(
            ctx,
            "Enter share",
            header=_(i18n_keys.TITLE__STR_OF_STR_SHARES_ENTERED).format(
                num=threshold, total=threshold - remaining[group_index]
            ),
            content=_(i18n_keys.TITLE__STR_OF_STR_SHARES_ENTERED_DESC).format(
                num=remaining[group_index]
            ),
            button=_(i18n_keys.BUTTON__CONTINUE),
        )


# async def _show_remaining_groups_and_shares(ctx: wire.GenericContext) -> None:
#     """
#     Show info dialog for Slip39 Advanced - what shares are to be entered.
#     """
#     shares_remaining = storage_recovery.fetch_slip39_remaining_shares()
#     # should be stored at this point
#     assert shares_remaining

#     groups = set()
#     first_entered_index = -1
#     for i, group_count in enumerate(shares_remaining):
#         if group_count < slip39.MAX_SHARE_COUNT:
#             first_entered_index = i

#     share = None
#     for index, remaining in enumerate(shares_remaining):
#         if 0 <= remaining < slip39.MAX_SHARE_COUNT:
#             m = storage.recovery_shares.fetch_group(index)[0]
#             if not share:
#                 share = slip39.decode_mnemonic(m)
#             identifier = m.split(" ")[0:3]
#             groups.add((remaining, tuple(identifier)))
#         elif remaining == slip39.MAX_SHARE_COUNT:  # no shares yet
#             identifier = storage.recovery_shares.fetch_group(first_entered_index)[
#                 0
#             ].split(" ")[0:2]
#             groups.add((remaining, tuple(identifier)))

#     assert share  # share needs to be set
#     return await layout.show_remaining_shares(
#         ctx, groups, shares_remaining, share.group_threshold
#     )
