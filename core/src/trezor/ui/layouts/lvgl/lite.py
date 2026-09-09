from trezorio import nfc

from trezor import utils, wire
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs import theme_path_png
from trezor.lvglui.scrs.common import FullSizeWindow, lv
from trezor.lvglui.scrs.nfc import (
    LITE_CARD_BLANK,
    LITE_CARD_CONNECT_FAILURE,
    LITE_CARD_FIND,
    LITE_CARD_NO_BACKUP,
    LITE_CARD_NOT_SAME,
    LITE_CARD_OPERATE_SUCCESS,
    LITE_CARD_PIN_ERROR,
    LITE_CARD_READ_FAILURE,
    LITE_CARD_RETRY_DECREMENT_FAILURE,
    LITE_CARD_RETRY_RESET_FAILURE,
    LITE_CARD_SET_PIN_FAILURE,
    LITE_CARD_UNSUPPORTED_WORD_COUNT,
    LITE_CARD_WITH_DATA,
    LITE_CARD_WRITE_FAILURE,
    SearchDeviceScreen,
    TransferDataScreen,
)
from trezor.lvglui.scrs.pinscreen import (
    request_existing_lite_pin,
    request_lite_pin_confirm,
)
from trezor.lvglui.scrs.wipe_device import WipeLiteCardTips

LITE_CARD_BUTTON_CONFIRM = 1
LITE_CARD_BUTTON_CANCLE = 0
MIFARE_MODEL_SEED_CARD = 10
MIFARE_MODEL_SEED_RING = 20


def _expected_mifare_model() -> int:
    if utils.get_current_backup_type() == utils.BACKUP_METHOD_RING:
        return MIFARE_MODEL_SEED_RING
    return MIFARE_MODEL_SEED_CARD


def _is_expected_mifare_model(model: int) -> bool:
    return model == _expected_mifare_model()


async def show_fullsize_window(
    ctx: wire.GenericContext,
    title,
    content,
    confirm_text,
    cancel_text=None,
    icon_path=None,
):
    screen = FullSizeWindow(
        title,
        content,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        icon_path=icon_path,
        anim_dir=0,
    )
    screen.btn_layout_ver()
    if hasattr(screen, "subtitle"):
        screen.subtitle.set_recolor(True)
    result = await ctx.wait(screen.request())
    return result


async def show_start_screen(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    screen = FullSizeWindow(
        _(i18n_keys.TITLE__GET_STARTED),
        _(
            i18n_keys.CONTENT__PLACE_LITE_DEVICE_FIGURE_CLICK_CONTINUE
            if is_lite
            else i18n_keys.SUBTITLE__RING_NFC_START
        ),
        confirm_text=_(i18n_keys.BUTTON__CONTINUE),
        cancel_text=_(i18n_keys.BUTTON__CANCEL),
        anim_dir=0,
        nav_back=False,
    )
    screen.img = lv.img(screen.content_area)
    screen.img.set_src(theme_path_png("nfc-start" if is_lite else "ring-nfc-start"))
    screen.img.align_to(
        screen.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 0  # if is_lite else 52
    )
    screen.content_area.set_style_min_height(660, 0)
    # screen.bnt_container.align_to(screen.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
    screen.update_btn_layout()
    return await ctx.wait(screen.request())


async def search_device(ctx: wire.GenericContext):
    search_scr = SearchDeviceScreen()
    return await ctx.wait(search_scr.request())


def format_retry_subtitle(retry_count: int) -> str:
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    if retry_count >= 10:
        return ""
    if retry_count == 0:
        try:
            return _(
                i18n_keys.TITLE__CARD_HAS_BEEN_PERMANENTLY_LOCKED
                if is_lite
                else i18n_keys.TITLE__RING_HAS_BEEN_PERMANENTLY_LOCKED
            )
        except IndexError:
            return "This card has been permanently locked."

    return _(
        i18n_keys.SUBTITLE__LITE_PIN_ERROR_DESC
        if is_lite
        else i18n_keys.SUBTITLE__RING_PIN_ERROR_DESC
    ).format(f"{retry_count}")


async def input_pin(ctx: wire.GenericContext, retry_count: int):
    return await request_existing_lite_pin(ctx, format_retry_subtitle(retry_count))


async def read_retry_count():
    try:
        return int(nfc.mifare_get_remaining_retry())
    except RuntimeError as exc:
        if __debug__:
            print(f"lite: failed to read remaining retry count: {exc}")
        return None


async def show_retry_error(ctx: wire.GenericContext, retry_count: int):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    if retry_count > 0:
        title = _(i18n_keys.TITLE__LITE_PIN_ERROR)
        content = _(
            i18n_keys.SUBTITLE__LITE_PIN_ERROR_DESC
            if is_lite
            else i18n_keys.SUBTITLE__RING_PIN_ERROR_DESC
        ).format(retry_count)
        icon_path = theme_path_png("triangle-error")
    else:
        title = _(
            i18n_keys.TITLE__CARD_HAS_BEEN_PERMANENTLY_LOCKED
            if is_lite
            else i18n_keys.TITLE__RING_HAS_BEEN_PERMANENTLY_LOCKED
        )
        content = _(
            i18n_keys.SUBTITLE__LITE_HAS_BEEN_RESET_DESC
            if is_lite
            else i18n_keys.SUBTITLE__RING_HAS_BEEN_RESET_DESC
        ).format(10)
        icon_path = theme_path_png("card-voided")

    await show_fullsize_window(
        ctx,
        title=title,
        content=content,
        confirm_text=_(i18n_keys.BUTTON__I_GOT_IT),
        icon_path=icon_path,
    )


async def show_connect_failed(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    return await show_fullsize_window(
        ctx,
        _(i18n_keys.TITLE__CONNECT_FAILED),
        _(
            i18n_keys.CONTENT__MAKE_SURE_THE_CARD_IS_CLOSE_TO_THE_UPPER_LEFT
            if is_lite
            else i18n_keys.CONTENT__MAKE_SURE_THE_RING_IS_CLOSE_TO_THE_UPPER_LEFT
        ),
        _(i18n_keys.BUTTON__TRY_AGAIN),
        _(i18n_keys.BUTTON__BACK),
        icon_path=theme_path_png("danger"),
    )


async def show_device_model_mismatch(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    return await show_fullsize_window(
        ctx,
        _(i18n_keys.TITLE__DEVICE_TYPE_MISMATCH),
        _(
            i18n_keys.CONTENT__MAKE_SURE_THE_CARD_IS_CLOSE_TO_THE_UPPER_LEFT
            if is_lite
            else i18n_keys.CONTENT__MAKE_SURE_THE_RING_IS_CLOSE_TO_THE_UPPER_LEFT
        ),
        _(i18n_keys.BUTTON__TRY_AGAIN),
        _(i18n_keys.BUTTON__BACK),
        icon_path=theme_path_png("danger"),
    )


def check_mifare_model():
    try:
        model = nfc.mifare_get_model()
    except RuntimeError as exc:
        if __debug__:
            print(f"lite: failed to read Mifare model: {exc}")
        return LITE_CARD_CONNECT_FAILURE

    if not _is_expected_mifare_model(model):
        if __debug__:
            print(
                f"lite: Mifare model mismatch: got {model}, expected {_expected_mifare_model()}"
            )
        return LITE_CARD_NOT_SAME

    return LITE_CARD_OPERATE_SUCCESS


async def show_interrupted(ctx: wire.GenericContext, is_import: bool = False):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    return await show_fullsize_window(
        ctx,
        _(
            i18n_keys.TITLE__IMPORT_INTERRUPTED
            if is_import
            else i18n_keys.TITLE__BACKUP_INTERRUPTED
        ),
        _(
            i18n_keys.CONTENT__MAKE_SURE_THE_CARD_IS_CLOSE_TO_THE_UPPER_LEFT
            if is_lite
            else i18n_keys.CONTENT__MAKE_SURE_THE_RING_IS_CLOSE_TO_THE_UPPER_LEFT
        ),
        _(i18n_keys.BUTTON__TRY_AGAIN),
        _(i18n_keys.BUTTON__BACK),
        icon_path=theme_path_png("danger"),
    )


async def show_connect_again(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    start_scr_again = FullSizeWindow(
        _(i18n_keys.TITLE__CONNECT_AGAIN),
        _(
            i18n_keys.CONTENT__KEEP_LITE_DEVICE_TOGETHER_BACKUP_COMPLETE
            if is_lite
            else i18n_keys.CONTENT__KEEP_RING_DEVICE_TOGETHER_BACKUP_COMPLETE
        ),
        confirm_text=_(i18n_keys.BUTTON__CONTINUE),
        cancel_text=_(i18n_keys.BUTTON__BACK),
        anim_dir=0,
    )
    start_scr_again.img = lv.img(start_scr_again.content_area)
    start_scr_again.img.set_src(
        theme_path_png("nfc-start" if is_lite else "ring-nfc-start")
    )
    start_scr_again.img.align_to(
        start_scr_again.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 0
    )
    return await ctx.wait(start_scr_again.request())


def _backup_device_name() -> str:
    if utils.get_current_backup_type() == utils.BACKUP_METHOD_RING:
        return "UKey Seed Ring"
    return "UKey Seed Card"


def _backup_pin_text(key: int) -> str:
    return _(key).format(_backup_device_name())


async def prompt_setup_new_backup_pin(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    return await show_fullsize_window(
        ctx,
        _backup_pin_text(i18n_keys.TITLE__SET_BACKUP_DEVICE_PIN),
        _backup_pin_text(i18n_keys.CONTENT__SET_NEW_BACKUP_DEVICE_PIN),
        _(i18n_keys.TITLE__SET_A_PIN),
        _(i18n_keys.BUTTON__BACK),
        icon_path=theme_path_png("nfc-start" if is_lite else "ring-nfc-start"),
    )


async def prompt_change_backup_pin(ctx: wire.GenericContext):
    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    return await show_fullsize_window(
        ctx,
        _backup_pin_text(i18n_keys.TITLE__CHANGE_BACKUP_DEVICE_PIN),
        _backup_pin_text(i18n_keys.CONTENT__CHANGE_BACKUP_DEVICE_PIN),
        _(i18n_keys.TITLE__CHANGE_PIN),
        _(i18n_keys.BUTTON__KEEP_CURRENT_PIN),
        icon_path=theme_path_png("nfc-start" if is_lite else "ring-nfc-start"),
    )


async def backup_with_lite(
    ctx: wire.GenericContext, mnemonics: bytes, recovery_check: bool = False
):
    nfc.pwr_ctrl(True)
    while True:
        start_flag = await show_start_screen(ctx)
        if start_flag == LITE_CARD_BUTTON_CONFIRM:
            while True:
                status_code = await search_device(ctx)
                if status_code == LITE_CARD_BUTTON_CANCLE:
                    break
                if status_code != LITE_CARD_FIND:
                    if __debug__:
                        print(f"lite: unexpected backup search status: {status_code}")
                    continue

                nfc.mifare_clear_session()
                model_status = check_mifare_model()
                if model_status == LITE_CARD_CONNECT_FAILURE:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break
                if model_status == LITE_CARD_NOT_SAME:
                    if (
                        await show_device_model_mismatch(ctx)
                        == LITE_CARD_BUTTON_CONFIRM
                    ):
                        continue
                    break

                # detect new-card tag (public page byte 3 == 0x00 means new card)
                is_new_card = False
                try:
                    is_new_card = bool(nfc.mifare_is_card_new())
                except RuntimeError as exc:
                    if __debug__:
                        print(f"lite: failed to read new-card flag: {exc}")

                retry_count = await read_retry_count()
                if retry_count is None:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break

                if is_new_card:
                    # New card: no existing pin, use default and proceed to prepare/write
                    pin = "000000"
                else:
                    pin = await input_pin(ctx, retry_count)
                    if not pin:
                        break

                prepare_scr = TransferDataScreen()
                prepare_scr.prepare_mifare_backup(pin)
                prepare_status = await ctx.wait(prepare_scr.request())

                if prepare_status == LITE_CARD_CONNECT_FAILURE:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break

                if prepare_status in (
                    LITE_CARD_RETRY_DECREMENT_FAILURE,
                    LITE_CARD_RETRY_RESET_FAILURE,
                    LITE_CARD_READ_FAILURE,
                ):
                    if await show_interrupted(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break

                if prepare_status == LITE_CARD_PIN_ERROR:
                    await show_retry_error(ctx, max(retry_count - 1, 0))
                    continue

                if str(prepare_status).startswith("63C"):
                    await show_retry_error(ctx, int(str(prepare_status)[-1], 16))
                    continue

                if prepare_status == LITE_CARD_WITH_DATA:
                    if not is_new_card:
                        confirm_screen = WipeLiteCardTips()
                        if not await ctx.wait(confirm_screen.request()):
                            break
                elif prepare_status != LITE_CARD_BLANK:
                    if __debug__:
                        print(
                            f"lite: unexpected backup prepare status: {prepare_status}"
                        )
                    break

                if is_new_card:
                    if (
                        await prompt_setup_new_backup_pin(ctx)
                        != LITE_CARD_BUTTON_CONFIRM
                    ):
                        break
                    new_pin = await request_lite_pin_confirm(
                        ctx,
                        _backup_pin_text(i18n_keys.TITLE__SET_BACKUP_DEVICE_PIN),
                    )
                elif await prompt_change_backup_pin(ctx) == LITE_CARD_BUTTON_CONFIRM:
                    new_pin = await request_lite_pin_confirm(
                        ctx,
                        _backup_pin_text(i18n_keys.TITLE__ENTER_NEW_BACKUP_DEVICE_PIN),
                    )
                else:
                    new_pin = pin

                if new_pin == LITE_CARD_BUTTON_CANCLE:
                    break

                if await show_connect_again(ctx) != LITE_CARD_BUTTON_CONFIRM:
                    break

                while True:
                    status_code = await search_device(ctx)
                    if status_code == LITE_CARD_BUTTON_CANCLE:
                        break
                    if status_code != LITE_CARD_FIND:
                        if __debug__:
                            print(
                                f"lite: unexpected backup write search status: {status_code}"
                            )
                        continue

                    nfc.mifare_clear_session()
                    model_status = check_mifare_model()
                    if model_status == LITE_CARD_CONNECT_FAILURE:
                        if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                            continue
                        break
                    if model_status == LITE_CARD_NOT_SAME:
                        if (
                            await show_device_model_mismatch(ctx)
                            == LITE_CARD_BUTTON_CONFIRM
                        ):
                            continue
                        break

                    write_scr = TransferDataScreen()
                    write_scr.write_mifare_backup(pin, mnemonics, new_pin)
                    write_status = await ctx.wait(write_scr.request())

                    if write_status == LITE_CARD_OPERATE_SUCCESS:
                        from trezor.ui.layouts import show_success

                        is_lite = (
                            utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
                        )
                        await show_success(
                            ctx,
                            _(i18n_keys.TITLE__BACK_UP_COMPLETE),
                            _(
                                i18n_keys.TITLE__BACKUP_COMPLETED_DESC
                                if is_lite
                                else i18n_keys.SUBTITLE__RING_BACKUP_COMPLETED
                            ),
                            header=_(i18n_keys.TITLE__BACK_UP_COMPLETE),
                            button=_(i18n_keys.BUTTON__CONTINUE),
                        )
                        return LITE_CARD_OPERATE_SUCCESS

                    if write_status == LITE_CARD_CONNECT_FAILURE:
                        if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                            continue
                        break

                    if write_status in (
                        LITE_CARD_RETRY_DECREMENT_FAILURE,
                        LITE_CARD_RETRY_RESET_FAILURE,
                        LITE_CARD_WRITE_FAILURE,
                        LITE_CARD_SET_PIN_FAILURE,
                    ):
                        if await show_interrupted(ctx) == LITE_CARD_BUTTON_CONFIRM:
                            continue
                        break

                    if write_status == LITE_CARD_PIN_ERROR:
                        await show_retry_error(ctx, max(retry_count - 1, 0))
                        break

                    if str(write_status).startswith("63C"):
                        await show_retry_error(ctx, int(str(write_status)[-1], 16))
                    break
        elif start_flag == LITE_CARD_BUTTON_CANCLE:
            from trezor.ui.layouts import show_lite_card_exit

            try:
                await show_lite_card_exit(
                    ctx,
                    content=_(i18n_keys.TITLE__EXIT_BACKUP_PROCESS_DESC),
                    header=_(i18n_keys.TITLE__EXIT_BACKUP_PROCESS),
                    subheader=None,
                    button_confirm=_(i18n_keys.BUTTON__EXIT),
                    button_cancel=_(i18n_keys.BUTTON__CANCEL),
                )

                return
            except wire.ActionCancelled:
                continue


async def backup_with_lite_import(ctx: wire.GenericContext):
    nfc.pwr_ctrl(True)
    while True:
        start_flag = await show_start_screen(ctx)
        if start_flag == LITE_CARD_BUTTON_CONFIRM:
            while True:
                status_code = await search_device(ctx)
                if status_code == LITE_CARD_BUTTON_CANCLE:
                    break
                if status_code != LITE_CARD_FIND:
                    if __debug__:
                        print(f"lite: unexpected import search status: {status_code}")
                    continue

                nfc.mifare_clear_session()
                model_status = check_mifare_model()
                if model_status == LITE_CARD_CONNECT_FAILURE:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break
                if model_status == LITE_CARD_NOT_SAME:
                    if (
                        await show_device_model_mismatch(ctx)
                        == LITE_CARD_BUTTON_CONFIRM
                    ):
                        continue
                    break

                # detect new-card flag and handle: new card has no backup data
                try:
                    is_new_card = bool(nfc.mifare_is_card_new())
                except RuntimeError as exc:
                    if __debug__:
                        print(f"lite: failed to read new-card flag: {exc}")
                    is_new_card = False

                if is_new_card:
                    is_lite = (
                        utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
                    )
                    retry_flag = await show_fullsize_window(
                        ctx,
                        _(
                            i18n_keys.TITLE__NO_BACKUP_ON_THIS_CARD
                            if is_lite
                            else i18n_keys.TITLE__NO_BACKUP_ON_THIS_RING
                        ),
                        _(
                            i18n_keys.TITLE__NO_BACKUP_ON_THIS_CARD_DESC
                            if is_lite
                            else i18n_keys.TITLE__NO_BACKUP_ON_THIS_RING_DESC
                        ),
                        _(i18n_keys.BUTTON__TRY_AGAIN),
                        _(i18n_keys.BUTTON__BACK),
                        icon_path=theme_path_png("danger"),
                    )
                    if retry_flag == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break

                retry_count = await read_retry_count()
                if retry_count is None:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break

                pin = await input_pin(ctx, retry_count)
                if not pin:
                    break

                import_scr = TransferDataScreen()
                import_scr.import_mifare_backup(pin)
                mnemonic_phrase = await ctx.wait(import_scr.request())

                if mnemonic_phrase == LITE_CARD_CONNECT_FAILURE:
                    if await show_connect_failed(ctx) == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break
                if mnemonic_phrase in (
                    LITE_CARD_RETRY_DECREMENT_FAILURE,
                    LITE_CARD_RETRY_RESET_FAILURE,
                    LITE_CARD_READ_FAILURE,
                ):
                    if (
                        await show_interrupted(ctx, is_import=True)
                        == LITE_CARD_BUTTON_CONFIRM
                    ):
                        continue
                    break
                is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
                if mnemonic_phrase == LITE_CARD_NO_BACKUP:
                    retry_flag = await show_fullsize_window(
                        ctx,
                        _(
                            i18n_keys.TITLE__NO_BACKUP_ON_THIS_CARD
                            if is_lite
                            else i18n_keys.TITLE__NO_BACKUP_ON_THIS_RING
                        ),
                        _(
                            i18n_keys.TITLE__NO_BACKUP_ON_THIS_CARD_DESC
                            if is_lite
                            else i18n_keys.TITLE__NO_BACKUP_ON_THIS_RING_DESC
                        ),
                        _(i18n_keys.BUTTON__TRY_AGAIN),
                        _(i18n_keys.BUTTON__BACK),
                        icon_path=theme_path_png("danger"),
                    )
                    if retry_flag == LITE_CARD_BUTTON_CONFIRM:
                        continue
                    break
                if mnemonic_phrase == LITE_CARD_UNSUPPORTED_WORD_COUNT:
                    await show_fullsize_window(
                        ctx,
                        _(i18n_keys.TITLE__UNSUPPORTED_RECOVERY_PHRASE),
                        _(
                            i18n_keys.TITLE__UNSUPPORTED_RECOVERY_PHRASE_DESC
                            if is_lite
                            else i18n_keys.TITLE__UNSUPPORTED_RECOVERY_PHRASE_DESC_RING
                        ),
                        _(i18n_keys.BUTTON__I_GOT_IT),
                        icon_path=theme_path_png("danger"),
                    )
                    break
                if mnemonic_phrase == LITE_CARD_PIN_ERROR:
                    await show_retry_error(ctx, max(retry_count - 1, 0))
                    continue
                if str(mnemonic_phrase).startswith("63C"):
                    await show_retry_error(ctx, int(str(mnemonic_phrase)[-1], 16))
                    continue
                if mnemonic_phrase:
                    return mnemonic_phrase

        if start_flag == LITE_CARD_BUTTON_CANCLE:
            return LITE_CARD_BUTTON_CANCLE

    return LITE_CARD_BUTTON_CANCLE
