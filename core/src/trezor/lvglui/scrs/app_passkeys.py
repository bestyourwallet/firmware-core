from typing import TYPE_CHECKING

from trezor import loop, utils
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs.components.button import NormalButton

from . import (
    font_GeistRegular26,
    font_GeistRegular30,
    font_GeistSemiBold30,
    font_GeistSemiBold64,
    lv,
    lv_theme,
    theme_path_png,
)
from .common import FullSizeWindow
from .components.container import ContainerFlexCol
from .components.listitem import DisplayItem
from .components.navigation import Navigation
from .widgets.style import StyleWrapper

if TYPE_CHECKING:
    from apps.webauthn.resident_credentials import Fido2Credential
    from typing import Iterator


def get_registered_credentials_count() -> int:
    from storage.resident_credentials import get_fido2_counter

    return get_fido2_counter()


def get_registered_credentials() -> Iterator[Fido2Credential]:
    from apps.webauthn.resident_credentials import find_all

    return find_all()


def delete_credential(index: int) -> None:
    from storage.resident_credentials import delete

    return delete(index)


class PasskeysGuide(lv.obj):
    def __init__(self, title, process_bar_value, **kwargs):
        super().__init__(lv.scr_act())
        self.set_size(lv.pct(100), lv.pct(100))
        self.align(lv.ALIGN.TOP_LEFT, 0, 0)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.DT_BG)
            .pad_all(0)
            .border_width(0)
            .radius(0),
            0,
        )
        self.nav_back = Navigation(self)  # , pos=(15, 44))
        self.nav_back.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        # self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)
        # self.nav_back.align(lv.ALIGN.TOP_MID, 15, 44)

        # self.process_bar = lv.bar(self)
        # self.process_bar.set_size(450, 4)
        # self.process_bar.align(lv.ALIGN.TOP_MID, 0, 44)
        # self.process_bar.add_style(
        #     StyleWrapper()
        #     .radius(0)
        #     .bg_color(lv_theme.PROCESS_BAR_BG),
        #     0,
        # )
        # self.process_bar.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.PROCESS_BAR_FG),
        #     lv.PART.INDICATOR | lv.STATE.DEFAULT
        # )
        # self.process_bar.set_value(process_bar_value, lv.ANIM.OFF)

        self.content_area = lv.obj(self)
        self.content_area.set_size(450, lv.SIZE.CONTENT)
        self.content_area.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 15, 0)
        # self.content_area.align(lv.ALIGN.TOP_MID, 0, 44)
        self.content_area.add_style(
            StyleWrapper()
            # .bg_color(lv_colors.UKEY_WHITE_3)
            .bg_opa(lv.OPA.TRANSP)
            .pad_all(0)
            .border_width(0)
            .radius(0)
            .max_height(622)
            .min_height(400),
            0,
        )
        self.content_area.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_BG),
            lv.PART.SCROLLBAR | lv.STATE.DEFAULT,
        )
        self.content_area.add_style(
            StyleWrapper().text_align(lv.TEXT_ALIGN.LEFT),
            0,
        )
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
        self.content_area.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        self.title = lv.label(self.content_area)
        self.title.set_width(450)
        self.title.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold64)
            .text_color(lv_theme.DT_TITLE_FG)
            .text_letter_space(-4)
            .text_line_space(-8),
            0,
        )
        self.title.set_text(title)
        self.title.align(lv.ALIGN.TOP_LEFT, 0, 10)

        step_text_style = (
            StyleWrapper()
            .text_font(font_GeistRegular30)
            .text_color(lv_theme.DT_TEXT_FG)
            .text_align_left()
            .text_letter_space(-1)
            .text_line_space(6)
            .width(450)
        )
        if "step1" in kwargs:
            self.step1 = lv.label(self.content_area)
            self.step1.add_style(step_text_style, 0)
            self.step1.set_long_mode(lv.label.LONG.WRAP)
            self.step1.set_text(f"1. {kwargs['step1']}")
            self.step1.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 28)
        if "step2" in kwargs:
            self.step2 = lv.label(self.content_area)
            self.step2.add_style(step_text_style, 0)
            self.step2.set_long_mode(lv.label.LONG.WRAP)
            self.step2.set_text(f"2. {kwargs['step2']}")
            self.step2.align_to(self.step1, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 16)
        if "step3" in kwargs:
            self.step3 = lv.label(self.content_area)
            self.step3.add_style(step_text_style, 0)
            self.step3.set_long_mode(lv.label.LONG.WRAP)
            self.step3.set_text(f"3. {kwargs['step3']}")
            self.step3.align_to(self.step2, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 16)
        if "step4" in kwargs:
            self.step4 = lv.label(self.content_area)
            self.step4.add_style(step_text_style, 0)
            self.step4.set_long_mode(lv.label.LONG.WRAP)
            self.step4.set_text(f"4. {kwargs['step4']}")
            self.step4.align_to(self.step3, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 16)

    def on_nav_back(self, event_obj):
        event = event_obj.code
        target = event_obj.get_target()
        if event == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if isinstance(target, lv.imgbtn):
                if hasattr(self, "nav_back") and target == self.nav_back.nav_btn:
                    # if hasattr(self, "cb_nva_back_event"):
                    #     self.cb_nva_back_event()
                    # if self.prev_scr is not None:  #
                    self.del_delayed(100)


class PasskeysRegister(PasskeysGuide):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_TITLE),
            50,
            step1=_(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_PLUG_IN),
            step2=_(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_GO_TO_WEBSITE),
            step3=_(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_SELECT_OPTION),
            step4=_(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_CONFIRM),
        )

        self.next_btn = NormalButton(self, "")
        self.next_btn.set_size(217, 80)
        self.next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -15, -15)
        self.next_btn.set_style_bg_img_src(theme_path_png("arrow-right-2"), 0)
        self.next_btn.add_style(StyleWrapper().bg_color(lv_theme.BTN_CANCEL_BG), 0)

        self.placeholder = NormalButton(self, "", False)
        self.placeholder.set_size(217, 80)
        self.placeholder.align(lv.ALIGN.BOTTOM_LEFT, 15, -15)
        self.placeholder.set_style_bg_img_src(theme_path_png("arrow-left-gray"), 0)
        self.placeholder.add_style(StyleWrapper().bg_color(lv_theme.BTN_CANCEL_BG), 0)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            utils.lcd_resume()
            if target == self.next_btn:
                self.del_delayed(100)
                PasskeysAuthenticate()


class PasskeysAuthenticate(PasskeysGuide):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TIPS_SECURITY_KEYS_AUTHENTICATE_TITLE),
            100,
            step1=_(i18n_keys.TIPS_SECURITY_KEYS_REGISTER_PLUG_IN),
            step2=_(i18n_keys.TIPS_SECURITY_KEYS_AUTHENTICATE_CHOOSE_OPTION),
            step3=_(i18n_keys.TIPS_SECURITY_KEYS_AUTHENTICATE_APPROVE),
        )

        self.next_btn = NormalButton(self, "")
        self.next_btn.set_size(217, 80)
        self.next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -15, -15)
        # self.next_btn.set_style_bg_img_src("A:res/arrow-right-2", 0)
        self.next_btn.set_style_bg_img_src(theme_path_png("arrow-right-2"), 0)
        self.next_btn.add_style(StyleWrapper().bg_color(lv_theme.BTN_CANCEL_BG), 0)

        self.back_btn = NormalButton(self, "")
        self.back_btn.set_size(217, 80)
        self.back_btn.align(lv.ALIGN.BOTTOM_LEFT, 15, -15)
        # self.back_btn.set_style_bg_img_src("A:res/arrow-left-2", 0)
        self.back_btn.set_style_bg_img_src(theme_path_png("arrow-left-2"), 0)
        self.back_btn.add_style(StyleWrapper().bg_color(lv_theme.BTN_CANCEL_BG), 0)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            utils.lcd_resume()
            if target == self.next_btn:
                self.del_delayed(100)
            elif target == self.back_btn:
                self.del_delayed(100)
                PasskeysRegister()


class PasskeysListItemBtn(DisplayItem):
    def __init__(self, parent, title, content, credential_index):
        super().__init__(parent, title, content, font=font_GeistSemiBold30)
        self.credential_index = credential_index
        self.app_name = title
        self.account_name = content
        self.add_style(
            StyleWrapper().min_height(100).pad_ver(17),
            0,
        )
        self.label_top.add_style(
            StyleWrapper().text_color(lv_theme.CONT_ITEM_FG),
            0,
        )
        self.label.add_style(
            StyleWrapper()
            .text_color(lv_theme.CONT_ITEM_SUB_FG)
            .text_font(font_GeistRegular26),
            0,
        )
        from .components.transition import DefaultTransition

        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_BG)
            .transform_height(-2)
            .transition(DefaultTransition()),
            lv.PART.MAIN | lv.STATE.PRESSED,
        )
        self.add_flag(lv.obj.FLAG.CLICKABLE)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)


class PasskeyDetailItem(DisplayItem):
    def __init__(self, parent, title, content):
        super().__init__(
            parent,
            title,
            content,
            font=font_GeistRegular26,
            bg_color=lv_theme.CONT_ITEM_BG,
            # lv_colors.UKEY_O_BLACK_3,
        )
        self.label.add_style(
            StyleWrapper()
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_font(font_GeistRegular30),
            0,
        )


async def request_credential_details(
    app_name: str, account_name: str, on_remove
) -> None:
    confirmed = await PasskeyDetails(app_name, account_name).request()
    if confirmed:
        confirmed = await ConfirmRemovePasskey().request()
        await loop.sleep(20)
        if confirmed:
            await on_remove()
            from trezor.ui.layouts.lvgl import show_popup

            await show_popup(
                _(i18n_keys.FIDO_REMOVE_KEY_SUCCESS_TITLE),
                icon=theme_path_png("success"),
                timeout_ms=2000,
            )


class PasskeyDetails(FullSizeWindow):
    def __init__(self, app_name: str, account_name: str):
        super().__init__(
            app_name,
            None,
            confirm_text=_(i18n_keys.BUTTON__REMOVE),
        )
        self.add_nav_back()
        # self.btn_yes.add_style(StyleWrapper().bg_color(lv_colors.UKEY_O_RED_1), 0)
        self.container = ContainerFlexCol(self.content_area, self.title, padding_row=0)
        # self.container.add_dummy(lv_theme.CONT_BG)
        self.app_name = PasskeyDetailItem(
            self.container,
            _(i18n_keys.LIST_KEY__APP_NAME__COLON),
            app_name,
        )
        self.account_name = PasskeyDetailItem(
            self.container,
            _(i18n_keys.LIST_KEY__ACCOUNT_NAME__COLON),
            account_name,
        )
        # self.container.add_dummy(lv_theme.CONT_BG)
        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.nav_back.nav_btn:
                self.channel.publish(0)
                self.destroy(50)
        elif code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def show_unload_anim(self):
        self.destroy(100)


class ConfirmRemovePasskey(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.FIDO_REMOVE_KEY_TITLE),
            _(i18n_keys.FIDO_REMOVE_KEY_DESC),
            confirm_text=_(i18n_keys.BUTTON__CONFIRM),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
        )
        self.add_nav_back()
        # self.btn_yes.add_style(StyleWrapper().bg_color(lv_colors.UKEY_O_RED_1), 0)
        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.nav_back.nav_btn:
                self.channel.publish(0)
                self.destroy(50)
        elif code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def show_unload_anim(self):
        self.destroy(100)


async def passkey_register_limit_reached() -> None:
    from trezor.ui.layouts.lvgl import show_warning
    from trezor.wire import DUMMY_CONTEXT
    from .homescreen import PasskeysManager, MainScreen

    await show_warning(
        DUMMY_CONTEXT,
        "passkey_register_limit_reached",
        header=_(i18n_keys.FIDO_ADD_KEY_LIMIT_REACHED_TITLE),
        content=_(i18n_keys.FIDO_ADD_KEY_LIMIT_REACHED_DESC),
        button=_(i18n_keys.FIDO_MANAGE_KEY_CTA_LABEL),
        icon=theme_path_png("danger"),
        btn_yes_bg_color=lv_theme.BTN_YES_BG,
    )

    PasskeysManager(MainScreen._instance)
