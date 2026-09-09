from trezor import config, wire
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs import lv_theme, theme_path_png
from trezor.lvglui.scrs.common import FullSizeWindow, lv
from trezor.lvglui.scrs.components.container import ContainerFlexCol
from trezor.lvglui.scrs.components.listitem import ListItemWithLeadingCheckbox

from apps.base import lock_device_if_unlocked
from apps.common.pin_constants import AttachCommon, PinResult, PinType

# UI Constants
USER_CANCELLED = 0
USER_CONFIRMED = 1
MAX_PASSPHRASE_LENGTH = 50


async def show_attach_to_pin_window(ctx):
    from trezor.lvglui.scrs.pinscreen import (
        request_passphrase_pin_confirm,
        request_passphrase_pin,
    )

    try:
        from trezor.crypto import se_acl16
        from apps.common.request_pin import (
            error_pin_invalid,
            request_pin_and_sd_salt,
            error_pin_used,
        )

        pin_screen_result = await show_pin_input_screen(ctx)
        if not pin_screen_result:
            return False
        curpin, _salt = await request_pin_and_sd_salt(
            ctx,
            _(i18n_keys.TITLE__ENTER_PIN),
            allow_fingerprint=False,
            standy_wall_only=True,
        )

        pinstatus, result = config.check_pin(curpin, None, PinType.USER_CHECK)
        if not pinstatus:
            return await error_pin_invalid(ctx)

        passphrase_pin = await request_passphrase_pin_confirm(ctx)
        if passphrase_pin == USER_CANCELLED:
            return False
        if curpin == passphrase_pin:
            return await error_pin_used(ctx)

        if len(passphrase_pin) >= AttachCommon.ATTACH_TO_PIN_MIN_LEN:
            passphrase_pin_str = (
                str(passphrase_pin)
                if not isinstance(passphrase_pin, str)
                else passphrase_pin
            )
            pinstatus, result = config.check_pin(
                passphrase_pin_str, None, PinType.PASSPHRASE_PIN_CHECK
            )
            if result == PinResult.PASSPHRASE_PIN_NO_MATCHED:
                current_space = se_acl16.get_pin_passphrase_space()
                if current_space < 1:
                    result = await show_hit_the_limit_window(ctx)
                    if result == USER_CONFIRMED:
                        while True:
                            passphrase_pin = await request_passphrase_pin(
                                ctx, _(i18n_keys.TITLE__ENTER_HIDDEN_WALLET_PIN)
                            )
                            if passphrase_pin == USER_CANCELLED:
                                return
                            passphrase_pin_str = (
                                str(passphrase_pin)
                                if not isinstance(passphrase_pin, str)
                                else passphrase_pin
                            )
                            pinstatus, result = config.check_pin(
                                passphrase_pin_str, None, PinType.PASSPHRASE_PIN_CHECK
                            )

                            if (
                                passphrase_pin_str != curpin
                                and result == PinResult.PASSPHRASE_PIN_ENTERED
                            ):
                                remove_status = await show_confirm_remove_pin_window(
                                    ctx
                                )
                                if remove_status == USER_CONFIRMED:
                                    passphrase_pin_str = (
                                        str(passphrase_pin)
                                        if not isinstance(passphrase_pin, str)
                                        else passphrase_pin
                                    )
                                    (
                                        remove_result,
                                        is_current,
                                    ) = se_acl16.delete_pin_passphrase(
                                        passphrase_pin_str
                                    )
                                    if remove_result:
                                        await showr_remove_pin_success_window(ctx)
                                        if is_current:
                                            return lock_device_if_unlocked()
                                        return True
                                    else:
                                        return False

                                elif remove_status == USER_CANCELLED:
                                    return
                            else:
                                try_again = await error_passphrase_pin_invalid(ctx)
                                if try_again == USER_CONFIRMED:
                                    continue
                                else:
                                    return
                    else:
                        return
                result = await show_not_attached_window(ctx)
                if result == USER_CANCELLED:
                    return False
                while True:
                    result = await show_attach_one_passphrase(ctx)
                    if result == USER_CANCELLED:
                        return False

                    from trezor.ui.layouts import request_passphrase_on_device

                    passphrase = await request_passphrase_on_device(
                        ctx, MAX_PASSPHRASE_LENGTH, min_len=1
                    )
                    if passphrase is None:
                        continue
                    if passphrase != USER_CANCELLED:
                        await show_save_your_passphrase_window(ctx)
                        curpin_str = (
                            str(curpin) if not isinstance(curpin, str) else curpin
                        )
                        passphrase_pin_str = (
                            str(passphrase_pin)
                            if not isinstance(passphrase_pin, str)
                            else passphrase_pin
                        )
                        passphrase_content_str = (
                            str(passphrase)
                            if not isinstance(passphrase, str)
                            else passphrase
                        )

                        save_result, save_status = se_acl16.save_pin_passphrase(
                            curpin_str, passphrase_pin_str, passphrase_content_str
                        )
                        if save_result:
                            await show_passphrase_set_and_attached_to_pin_window(ctx)
                            return True
                        else:
                            return False
            else:
                if passphrase_pin == curpin:
                    await show_pin_already_used_window(ctx)
                else:
                    next_status = await show_has_attached_window(ctx)
                    if next_status == USER_CONFIRMED:
                        while True:
                            passphrase_result = await show_attach_one_passphrase(ctx)
                            if passphrase_result == USER_CANCELLED:
                                return False
                            from trezor.ui.layouts import request_passphrase_on_device

                            passphrase = await request_passphrase_on_device(
                                ctx, MAX_PASSPHRASE_LENGTH, min_len=1
                            )
                            if passphrase is None:
                                continue
                            if passphrase != USER_CANCELLED:
                                await show_save_your_passphrase_window(ctx)
                                curpin_str = (
                                    str(curpin)
                                    if not isinstance(curpin, str)
                                    else curpin
                                )
                                passphrase_pin_str = (
                                    str(passphrase_pin)
                                    if not isinstance(passphrase_pin, str)
                                    else passphrase_pin
                                )
                                passphrase_content_str = (
                                    str(passphrase)
                                    if not isinstance(passphrase, str)
                                    else passphrase
                                )
                                save_result, save_status = se_acl16.save_pin_passphrase(
                                    curpin_str,
                                    passphrase_pin_str,
                                    passphrase_content_str,
                                )
                                if not save_result:
                                    return False
                                if save_status:
                                    config.check_pin(
                                        curpin_str, None, PinType.PASSPHRASE_PIN
                                    )
                                await show_passphrase_set_and_attached_to_pin_window(
                                    ctx, save_result
                                )
                                if save_status:
                                    return lock_device_if_unlocked()
                                return True

                    elif next_status == USER_CANCELLED:
                        remove_status = await show_confirm_remove_pin_window(ctx)
                        if remove_status == USER_CONFIRMED:
                            passphrase_pin_str = (
                                str(passphrase_pin)
                                if not isinstance(passphrase_pin, str)
                                else passphrase_pin
                            )
                            remove_result, is_current = se_acl16.delete_pin_passphrase(
                                passphrase_pin_str
                            )
                            if remove_result:
                                await showr_remove_pin_success_window(ctx)
                                if is_current:
                                    return lock_device_if_unlocked()
                                return True
                            else:
                                return False
                    else:
                        return False

        return True
    except Exception:
        return False


async def error_passphrase_pin_invalid(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.TITLE__WRONG_PIN),
        _(i18n_keys.SUBTITLE__SET_PIN_WRONG_PIN),
        confirm_text=_(i18n_keys.BUTTON__TRY_AGAIN),
        cancel_text=_(i18n_keys.BUTTON__CLOSE),
        # icon_path="A:/res/danger.png",
        icon_path=theme_path_png("danger"),
        anim_dir=0,
    )
    return await ctx.wait(screen.request())


# PIN is not be attached
async def show_not_attached_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__PIN_NOT_ATTACHED),
        _(i18n_keys.PASSPHRASE__PIN_NOT_ATTACHED_DESC),
        confirm_text=_(i18n_keys.PASSPHRASE__PIN_ATTACHED_ONE),
        anim_dir=0,
    )

    # processing = False
    #
    # def on_close_clicked(e):
    #     nonlocal processing
    #     if e.code == lv.EVENT.CLICKED and not processing:
    #         processing = True
    #         screen.show_dismiss_anim()
    #         screen.channel.publish(USER_CANCELLED)
    #
    # screen.add_nav_back_right()
    # screen.nav_back_right.add_event_cb(on_close_clicked, lv.EVENT.CLICKED, None)

    result = await ctx.wait(screen.request())
    return result


async def show_has_attached_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__PIN_ATTACHED),
        _(i18n_keys.PASSPHRASE__PIN_ATTACHED_DESC),
        confirm_text=_(i18n_keys.PASSPHRASE__PIN_UPDATE),
        cancel_text=_(i18n_keys.PASSPHRASE__PIN_REMOVE),
        anim_dir=0,
    )

    # processing = False
    #
    # def on_close_clicked(e):
    #     nonlocal processing
    #     if e.code == lv.EVENT.CLICKED and not processing:
    #         processing = True
    #         screen.show_dismiss_anim()
    #         screen.channel.publish(-1)
    #
    # screen.add_nav_back_right()
    # screen.nav_back_right.add_event_cb(on_close_clicked, lv.EVENT.CLICKED, None)
    # close_btn.add_event_cb(on_close_clicked, lv.EVENT.CLICKED, None)
    # screen.btn_no.enable(lv_colors.UKEY_O_RED_1, text_color=lv_colors.BLACK)
    result = await ctx.wait(screen.request())
    return result


async def show_pin_already_used_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__PIN_USED),
        _(i18n_keys.PASSPHRASE__PIN_USED_DESC),
        confirm_text=_(i18n_keys.BUTTON__CLOSE),
        icon_path=theme_path_png("danger"),  # "A:/res/danger.png",
        anim_dir=0,
    )
    result = await ctx.wait(screen.request())
    return result


# Hit the limit
async def show_hit_the_limit_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__PIN_HIT_LIMIT),
        _(i18n_keys.PASSPHRASE__PIN_HIT_LIMIT_DESC),
        confirm_text=_(i18n_keys.PASSPHRASE__PIN_REMOVE),
        cancel_text=_(i18n_keys.BUTTON__CLOSE),
        icon_path=theme_path_png("danger"),
        anim_dir=0,
    )
    screen.btn_yes.enable()  # lv_colors.UKEY_O_RED_1, text_color=lv_colors.BLACK)
    result = await ctx.wait(screen.request())
    return result


# confirm remove pin
async def show_confirm_remove_pin_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__REMOVE),
        _(i18n_keys.PASSPHRASE__REMOVE_DESC),
        confirm_text=_(i18n_keys.BUTTON__REMOVE),
        cancel_text=_(i18n_keys.BUTTON__CANCEL),
        icon_path=theme_path_png("warning"),
        anim_dir=0,
    )
    screen.btn_yes.enable()  # lv_colors.UKEY_O_RED_1, text_color=lv_colors.BLACK)
    result = await ctx.wait(screen.request())
    return result


async def showr_remove_pin_success_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__REMOVE_SUCCESSFUL),
        "",
        confirm_text=_(i18n_keys.BUTTON__DONE),
        icon_path=theme_path_png("success"),
        anim_dir=0,
    )
    result = await ctx.wait(screen.request())
    return result


async def show_save_your_passphrase_window(ctx: wire.Context):
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__SAVE),
        _(i18n_keys.PASSPHRASE__SAVE_DESC),
        confirm_text=_(i18n_keys.PASSPHRASE__UNDERSTAND),
        icon_path=theme_path_png("warning"),
        anim_dir=0,
    )
    result = await ctx.wait(screen.request())
    return result


async def show_passphrase_set_and_attached_to_pin_window(
    ctx: wire.Context, restart: bool = False
):
    class PassphraseSetWindow(FullSizeWindow):
        def __init__(self, restart: bool):
            super().__init__(
                _(i18n_keys.PASSPHRASE__SET),
                _(i18n_keys.PASSPHRASE__SET_DESC),
                confirm_text=_(i18n_keys.BUTTON__DONE),
                icon_path=theme_path_png("success"),
                anim_dir=0,
                nav_back=not restart,
            )
            self.title.set_style_text_line_space(0, 0)

            if restart:
                self.container = ContainerFlexCol(
                    self.content_area,
                    self.subtitle,
                    padding_row=8,
                    clip_corner=False,
                )
                self.checkbox_item = ListItemWithLeadingCheckbox(
                    self.container,
                    _(i18n_keys.ITEM__PASSPHRASE__SET_CONFIRM),
                    radius=12,
                )

                self.btn_yes.disable()

                self.container.add_event_cb(
                    self.on_value_changed, lv.EVENT.VALUE_CHANGED, None
                )

        def on_value_changed(self, event_obj):
            code = event_obj.code
            target = event_obj.get_target()
            if code == lv.EVENT.VALUE_CHANGED:
                if target == self.checkbox_item.checkbox:
                    if target.get_state() & lv.STATE.CHECKED:
                        self.checkbox_item.enable_bg_color()
                        self.btn_yes.enable()
                    else:
                        self.checkbox_item.enable_bg_color(False)
                        self.btn_yes.disable()

    screen = PassphraseSetWindow(restart=restart)
    result = await ctx.wait(screen.request())
    return result


async def show_attach_one_passphrase(ctx: wire.Context):
    class AttachOnePassphraseTips(FullSizeWindow):
        def __init__(self):
            title = _(i18n_keys.PASSPHRASE__ATTACH_ONE_PASSPHRASE)
            super().__init__(
                title,
                None,
                _(i18n_keys.BUTTON__SLIDE_TO_CONFIRM),
                _(i18n_keys.BUTTON__CANCEL),
                hold_confirm=True,
                primary_color=lv_theme.APP_CORRECT_BG,
            )
            self.container = ContainerFlexCol(
                self.content_area,
                self.title,
                padding_row=8,
                clip_corner=False,
            )
            self.item1 = ListItemWithLeadingCheckbox(
                self.container,
                _(i18n_keys.PASSPHRASE__ATTACH_ONE_PASSPHRASE_DESC1),
                radius=12,
            )
            self.item2 = ListItemWithLeadingCheckbox(
                self.container,
                _(i18n_keys.PASSPHRASE__ATTACH_ONE_PASSPHRASE_DESC2),
                radius=12,
            )

            self.slider_enable(False)
            self.container.add_event_cb(
                self.on_value_changed, lv.EVENT.VALUE_CHANGED, None
            )
            self.cb_cnt = 0

        def slider_enable(self, enable: bool = True):
            if enable:
                self.slider.add_flag(lv.obj.FLAG.CLICKABLE)
                self.slider.enable()
            else:
                self.slider.clear_flag(lv.obj.FLAG.CLICKABLE)
                self.slider.enable(False)

        def on_value_changed(self, event_obj):
            code = event_obj.code
            target = event_obj.get_target()
            if code == lv.EVENT.VALUE_CHANGED:
                if target == self.item1.checkbox:
                    if target.get_state() & lv.STATE.CHECKED:
                        self.item1.enable_bg_color()
                        self.cb_cnt += 1
                    else:
                        self.item1.enable_bg_color(False)
                        self.cb_cnt -= 1
                elif target == self.item2.checkbox:
                    if target.get_state() & lv.STATE.CHECKED:
                        self.item2.enable_bg_color()
                        self.cb_cnt += 1
                    else:
                        self.item2.enable_bg_color(False)
                        self.cb_cnt -= 1
                if self.cb_cnt == 2:
                    self.slider_enable()
                elif self.cb_cnt < 2:
                    self.slider_enable(False)

    screen = AttachOnePassphraseTips()
    result = await ctx.wait(screen.request())
    return result


async def show_pin_input_screen(ctx: wire.Context):
    """Display the PIN input screen for attaching passphrase to PIN"""
    screen = FullSizeWindow(
        _(i18n_keys.PASSPHRASE__ATTACH_TO_PIN),
        _(i18n_keys.ITEM__ATTACH_TO_PIN_DESC),
        confirm_text=_(i18n_keys.BUTTON__CONTINUE),
        anim_dir=0,
    )

    pin_container = lv.obj(screen.content_area)
    pin_container.set_size(lv.pct(100), lv.SIZE.CONTENT)
    pin_container.align_to(screen.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
    pin_container.set_style_bg_opa(0, 0)
    pin_container.set_style_border_width(0, 0)
    pin_container.set_style_pad_all(0, 0)

    # pin_img = lv.img(pin_container)
    # pin_img.set_src(theme_path_default("attach_to_pin_display.png"))
    # pin_img.align_to(screen.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 48)

    device_img = lv.img(screen.content_area)
    device_img.set_src(theme_path_png("attach-to-pin-guide"))
    device_img.align_to(screen.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
    screen.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    screen.content_area.set_style_max_height(610, 0)
    # screen.btn_yes.add_style(
    #     StyleWrapper()
    #     .bg_opa(20)
    #     , 0
    # )

    # processing = False
    #
    # def on_close_clicked(e):
    #     nonlocal processing
    #     if e.code == lv.EVENT.CLICKED and not processing:
    #         processing = True
    #         screen.show_dismiss_anim()
    #         screen.channel.publish(False)
    #
    # screen.add_nav_back_right()
    # screen.nav_back_right.add_event_cb(on_close_clicked, lv.EVENT.CLICKED, None)

    result = await ctx.wait(screen.request())
    return result
