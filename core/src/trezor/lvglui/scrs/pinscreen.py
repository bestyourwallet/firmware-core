from trezor import loop, uart, utils
from trezor.qr import close_camera

from ..i18n import gettext as _, keys as i18n_keys
from . import (
    font_GeistRegular26,
    font_GeistRegular30,
    font_GeistSemiBold48,
    lv_theme,
    theme_path_png,
)
from .common import AnimScreen, FullSizeWindow, lv  # noqa: F401,F403
from .components.container import ContainerFlexCol
from .components.keyboard import IndexKeyboard, NumberKeyboard, PassphraseKeyboard
from .components.listitem import ListItemWithLeadingCheckbox
from .widgets.style import StyleWrapper


class PinTip(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__SETUP_CREATE_ENABLE_PIN_PROTECTION),
            _(i18n_keys.SUBTITLE__SETUP_CREATE_ENABLE_PIN_PROTECTION),
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            anim_dir=0,
            nav_back=False,
        )
        self.container = ContainerFlexCol(
            self.content_area,
            self.subtitle,
            bg_opa=lv.OPA.TRANSP,
            pos=(0, 30),
            padding_row=10,
            clip_corner=False,
        )
        # self.container.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.item1 = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.CHECK__SETUP_SET_A_PIN__1),
            radius=12,
        )
        self.item2 = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.CHECK__SETUP_SET_A_PIN__2),
            radius=12,
        )
        # self.btn = NormalButton(self, _(i18n_keys.BUTTON__CONTINUE), False)
        self.btn_yes.disable()
        self.container.add_event_cb(self.eventhandler, lv.EVENT.VALUE_CHANGED, None)
        # self.btn_yes.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        self.cb_cnt = 0
        self.update_btn_layout()

    def eventhandler(self, event_obj: lv.event_t):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if target == self.btn_yes:
                self.channel.publish(1)
                self.destroy()
            # elif target == self.nav_back or target == self.nav_back.nav_btn:
            #     self.show_dismiss_anim()
            #     self.channel.publish(0)
        elif code == lv.EVENT.VALUE_CHANGED:
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
                self.btn_yes.enable(
                    bg_color=lv_theme.BTN_YES_BG, text_color=lv_theme.BTN_YES_FG
                )
            elif self.cb_cnt < 2:
                self.btn_yes.disable()


class InputNum(FullSizeWindow):
    _instance = None

    @classmethod
    def get_window_if_visible(cls) -> "InputNum" | None:
        try:
            if cls._instance is not None and cls._instance.is_visible():
                return cls._instance
        except Exception:
            pass
        return None

    def __init__(self, **kwargs):
        super().__init__(
            title=kwargs.get("title") or _(i18n_keys.TITLE__ENTER_PIN),
            subtitle=kwargs.get("subtitle", ""),
            anim_dir=0,
        )
        self.__class__._instance = self

        self.title.text.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_align_center()
            .text_letter_space(0),
            0,
        )
        self.title.align(lv.ALIGN.TOP_MID, 0, 24)

        if self.subtitle.get_text() != "":
            self.subtitle.add_style(
                StyleWrapper()
                .text_font(font_GeistRegular26)
                .max_width(368)
                .text_color(lv_theme.APP_COMP_FG)
                .bg_color(lv_theme.APP_ERROR_BG)
                .bg_opa(lv.OPA.COVER)
                .pad_hor(8)
                .pad_ver(16)
                .radius(40)
                .text_align_center(),
                0,
            )

            title_height = self.title.get_height()
            subtitle_y = 40 if title_height > 60 else 70
            self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, subtitle_y)
            self.subtitle.move_foreground()

        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = IndexKeyboard(
            self, min_len=1, max_len=11, is_pin=kwargs.get("is_pin", True)
        )
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)

        self.keyboard.ta.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP),
            0,
        )

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            if self.keyboard.ta.get_text() != "":
                self.subtitle.set_text("")
                self.subtitle.remove_style_all()

            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if input.startswith("#"):
                input = input[1:]
            if len(input) < 1:
                return
            self.channel.publish(input)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.destroy(250)


class InputPin(FullSizeWindow):

    _instance = None
    _pending_fingerprint_subtitle = ""

    @classmethod
    def get_window_if_visible(cls) -> "InputPin" | None:
        try:
            if cls._instance is not None and cls._instance.is_visible():
                return cls._instance
        except Exception:
            pass
        return None

    @classmethod
    def set_fingerprint_subtitle(cls, subtitle: str) -> None:
        cls._pending_fingerprint_subtitle = subtitle
        window = cls.get_window_if_visible()
        if window is not None:
            window.change_subtitle(subtitle)

    @classmethod
    def clear_pending_fingerprint_subtitle(cls) -> None:
        cls._pending_fingerprint_subtitle = ""

    @staticmethod
    def fingerprint_subtitle(level: int) -> str:
        if level == 1:
            return _(i18n_keys.MSG__FINGERPRINT_NOT_RECOGNIZED_TRY_AGAIN)
        if level == 2:
            return _(i18n_keys.MSG__YOUR_PIN_CODE_REQUIRED_TO_ENABLE_FINGERPRINT_UNLOCK)
        if level == 3:
            return _(i18n_keys.MSG__PUT_FINGER_ON_THE_FINGERPRINT)
        if level == 4:
            return _(i18n_keys.MSG__CLEAN_FINGERPRINT_SENSOR_AND_TRY_AGAIN)
        return ""

    def __init__(self, **kwargs):
        subtitle = kwargs.get("subtitle", "")
        if self.__class__._pending_fingerprint_subtitle and not subtitle:
            subtitle = self.__class__._pending_fingerprint_subtitle
        self.__class__._pending_fingerprint_subtitle = ""
        nav_back = kwargs.get("nav_back", True)
        super().__init__(
            title=kwargs.get("title") or _(i18n_keys.TITLE__ENTER_PIN),
            subtitle=subtitle,
            anim_dir=0,
            nav_back=nav_back,
        )
        # print('TITLE__ENTER_PIN:', _(i18n_keys.TITLE__ENTER_PIN), "<<<", subtitle)
        # title = kwargs.get("title")
        self.__class__._instance = self
        self.allow_fingerprint = kwargs.get("allow_fingerprint", True)
        self.standy_wall_only = kwargs.get("standy_wall_only", False)
        self.min_len = kwargs.get("min_len", 4)
        # self.title.add_style(
        #     StyleWrapper()
        #     .text_font(font_GeistSemiBold48)
        #     .text_align_center()
        #     .text_letter_space(0)
        #     , 0,
        # )
        self.title.set_size(450, lv.SIZE.CONTENT)
        self.title.text.set_size(450, lv.SIZE.CONTENT)
        self.title.text.add_style(
            StyleWrapper().text_align_center().text_letter_space(0), 0
        )
        self.title.align(lv.ALIGN.TOP_MID, 0, 24 if nav_back else 80)

        standard_wallet_text = _(i18n_keys.CONTENT__PIN_FOR_STANDARD_WALLET)
        is_standard_wallet = subtitle == standard_wallet_text
        self.subtitle.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular26)
            .max_width(368)
            .text_color(lv_theme.INPUT_TIP_FG)
            .bg_color(
                lv_theme.DT_BG
                if is_standard_wallet or not subtitle
                else lv_theme.APP_ERROR_BG
            )
            .bg_opa(lv.OPA.COVER)
            .pad_hor(8)
            .pad_ver(16)
            .radius(40)
            .text_align_center(),
            0,
        )
        self.subtitle.set_text(subtitle)
        title_height = self.title.get_height()
        if is_standard_wallet:
            subtitle_y = 16 if title_height <= 60 else 8
        else:
            subtitle_y = 24 if title_height > 60 else 70
        self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, subtitle_y)
        self.subtitle.set_text(subtitle)
        # self._show_fingerprint_prompt_if_necessary()
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = NumberKeyboard(self, min_len=self.min_len)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)

        # self.keyboard.ta.add_style(
        #     StyleWrapper()
        #     .bg_opa(lv.OPA.TRANSP)
        #     ,0,
        # )

    def change_subtitle(self, subtitle: str):
        from apps.common import passphrase

        # if standy_wall_only :
        if (
            subtitle == _(i18n_keys.CONTENT__PIN_FOR_STANDARD_WALLET)
            and passphrase.is_passphrase_pin_enabled()
        ):
            self.subtitle.set_style_bg_color(lv_theme.DT_BG, 0)
            title_height = self.title.get_height()
            offset_y = 16 if title_height <= 60 else 8
            self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, offset_y)
        else:
            self.subtitle.set_style_bg_color(
                lv_theme.APP_ERROR_BG if subtitle else lv_theme.DT_BG, 0
            )
            title_height = self.title.get_height()
            offset_y = 24 if title_height > 60 else 70
            self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, offset_y)

        self.subtitle.set_text(subtitle)

        keyboard_text = self.keyboard.ta.get_text()
        if keyboard_text:
            if subtitle:
                if subtitle == _(i18n_keys.CONTENT__PIN_FOR_STANDARD_WALLET):
                    self.keyboard.ta.align(lv.ALIGN.TOP_MID, 0, 240)
                else:
                    self.keyboard.ta.align_to(
                        self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 10
                    )
            else:
                self.keyboard.ta.align(lv.ALIGN.TOP_MID, 0, 218)

    # def _show_fingerprint_prompt_if_necessary(self):
    #     from . import fingerprints

    #     if self.allow_fingerprint and fingerprints.is_available():
    #         self.fingerprint_prompt = lv.img(self.content_area)
    #         # self.fingerprint_prompt.set_src(theme_path_default("prompt_fingerprint-prompt.png"))
    #         self.fingerprint_prompt.set_pos(414, 30)
    #         self.anim = lv.anim_t()
    #         self.anim.init()
    #         self.anim.set_var(self.fingerprint_prompt)
    #         self.anim.set_values(414, 404)
    #         self.anim.set_time(100)
    #         self.anim.set_playback_delay(10)
    #         self.anim.set_playback_time(100)
    #         self.anim.set_repeat_delay(20)
    #         self.anim.set_repeat_count(2)
    #         self.anim.set_path_cb(lv.anim_t.path_ease_in_out)
    #         self.anim.set_custom_exec_cb(lambda _a, val: self.anim_set_x(val))

    def anim_set_x(self, val):
        try:
            self.fingerprint_prompt.set_x(val)
        except Exception:
            pass

    def refresh_fingerprint_prompt(self):
        if hasattr(self, "fingerprint_prompt"):
            try:
                self.fingerprint_prompt.delete()
                del self.fingerprint_prompt
                del self.anim
                self.change_subtitle("")
            except Exception:
                pass

    def show_fp_failed_prompt(self, level: int = 0):
        if level:
            self.change_subtitle(self.fingerprint_subtitle(level))
        if hasattr(self, "fingerprint_prompt"):
            lv.anim_t.start(self.anim)

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            current_input = self.keyboard.ta.get_text()
            if current_input != "":
                from apps.common import passphrase

                if self.standy_wall_only and passphrase.is_passphrase_pin_enabled():
                    self.change_subtitle(_(i18n_keys.CONTENT__PIN_FOR_STANDARD_WALLET))
                else:
                    self.change_subtitle("")
            return
        elif code == lv.EVENT.READY:
            input_text = self.keyboard.ta.get_text()
            if len(input_text) < self.min_len:
                return
            self.channel.publish(input_text)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)
        self.clean()
        self.destroy(250)


class InputLitePin(FullSizeWindow):
    def __init__(self, **kwargs):
        subtitle = kwargs.get("subtitle", "")
        is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
        super().__init__(
            title=kwargs.get("title")
            or _(
                i18n_keys.TITLE__ENTER_UKEY_LITE_PIN
                if is_lite
                else i18n_keys.TITLE__ENTER_UKEY_RING_PIN
            ),
            subtitle=subtitle,
            anim_dir=0,
        )
        self.title.text.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_align_center()
            .text_letter_space(0),
            0,
        )
        self.title.align(lv.ALIGN.TOP_MID, 0, 0)
        self.subtitle.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular26)
            .max_width(380)
            .text_color(lv_theme.INPUT_TIP_FG)
            .bg_color(lv_theme.APP_ERROR_BG if subtitle else lv_theme.DT_BG)
            .bg_opa(lv.OPA.COVER)
            .pad_hor(8)
            .pad_ver(16)
            .radius(40)
            .text_align_center(),
            0,
        )
        self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 70)
        self.subtitle.set_text(subtitle)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = NumberKeyboard(self, max_len=6, min_len=6)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)
        self.keyboard.ta.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP),
            0,
        )

    def change_subtitle(self, subtitle: str):
        self.subtitle.set_style_bg_color(
            lv_theme.APP_ERROR_BG if subtitle else lv_theme.DT_BG, 0
        )
        self.subtitle.set_text(subtitle)

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            if hasattr(self, "subtitle"):
                if self.keyboard.ta.get_text() != "":
                    self.subtitle.add_flag(lv.obj.FLAG.HIDDEN)
                elif self.subtitle.has_flag(lv.obj.FLAG.HIDDEN):
                    self.subtitle.clear_flag(lv.obj.FLAG.HIDDEN)
            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if len(input) < 6:
                return
            self.channel.publish(input)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.destroy()


class InputTiSerialScan(FullSizeWindow):
    SCAN_STATE_IDLE = 0
    SCAN_STATE_SCANNING = 1
    SCAN_STATE_ERROR = 2

    def __init__(self):
        if not hasattr(self, "_init"):
            self._init = True
            super().__init__(
                None,
                None,
            )
        else:
            if not self.is_visible():
                self._load_scr(self)
            return
        self.camera_bg = lv.img(self)
        self.camera_bg.set_src(theme_path_png("camera-bg"))
        self.camera_bg.align(lv.ALIGN.TOP_MID, 0, 155)

        self.btn = lv.obj(self)
        self.btn.add_style(
            StyleWrapper()
            .border_width(0)
            .bg_img_src(theme_path_png("light-close"))
            .bg_opa(lv.OPA.TRANSP),
            0,
        )
        # self.btn.add_state(lv.STATE.CHECKED)
        self.btn.add_event_cb(self.on_event, lv.EVENT.CLICKED, None)
        self.btn.align_to(self.camera_bg, lv.ALIGN.OUT_BOTTOM_MID, 0, 134)

        # Start QR code scanning
        from trezor import qr

        qr.ti_scan_qr(self)
        self.scan_state = self.SCAN_STATE_SCANNING
        self.qr_data = None

    def on_event(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.btn:
                if self.btn.has_state(lv.STATE.CHECKED):
                    self.btn.add_style(
                        StyleWrapper().bg_img_src(theme_path_png("light-close")),
                        0,
                    )
                    self.btn.clear_state(lv.STATE.CHECKED)
                    uart.flashled_close()
                else:
                    self.btn.add_style(
                        StyleWrapper().bg_img_src(theme_path_png("light-open")),
                        0,
                    )
                    self.btn.add_state(lv.STATE.CHECKED)
                    uart.flashled_open()

    async def transition_to(self, state):
        """Handle state transitions during QR code scanning"""
        self.scan_state = state
        # You can add UI updates here based on the state

    async def on_process_update(self, percent):
        """Handle progress updates during QR code scanning"""
        # You can add progress indicator updates here

    async def on_qr_scanned(self, qr_data):
        """Handle QR code scanning result"""
        if qr_data:
            self.qr_data = qr_data
        # Hide the scan layer before returning the result so the parent page can
        # update without racing the direct camera overlay on screen.
        self.add_flag(lv.obj.FLAG.HIDDEN)
        self.on_nav_back(None)
        if qr_data:
            await loop.sleep(20)
            self.channel.publish(qr_data)

    # def on_ready(self, event_obj):
    #     input_text = self.keyboard.ta.get_text()
    #     self.channel.publish(input_text)
    #     self.keyboard.ta.set_text("")
    #     self.destroy(200)

    def on_nav_back(self, event_obj):
        uart.flashled_close()
        close_camera()
        if self.qr_data is None:
            self.channel.publish(None)
        self.destroy(200)


class InputTiSerial(FullSizeWindow):
    def __init__(self, result: str | None = None, min_len: int = 0):
        super().__init__(_(i18n_keys.TITLE__TI_ENTER_SERIAL), None, anim_dir=0)
        # self.add_nav_back()
        # self.title.add_style(
        #     StyleWrapper()
        #     .text_color(lv_theme.DT_TITLE_FG)
        #     .text_align_left()
        #     .text_letter_space(-1)
        #     .text_line_space(0)
        #     , 0,
        # )
        serial_len = 50
        # self.rti_btn = lv.imgbtn(self)
        # self.rti_btn.set_size(48, 48)
        # self.rti_btn.set_ext_click_area(100)
        # self.rti_btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        # self.rti_btn.add_style(StyleWrapper().bg_img_src(theme_path_png("rti-scan")), 0)
        # self.rti_btn.align(lv.ALIGN.TOP_RIGHT, -12, 40)
        # self.rti_btn.add_event_cb(self.on_rti_scan, lv.EVENT.CLICKED, None)
        self.title.text.add_style(
            StyleWrapper().text_font(font_GeistRegular30),
            0,
        )
        self.keyboard = PassphraseKeyboard(self, serial_len, min_len)
        if result is not None:
            self.keyboard.ta.set_text(result)
            self.keyboard.ta.set_cursor_pos(lv.TEXTAREA_CURSOR.LAST)
            self.keyboard.update_ok_button_state()
            self.keyboard.update_count_tips()
        self.keyboard.add_event_cb(self.on_ready, lv.EVENT.READY, None)

        self.keyboard.ta.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 30)
        # self.keyboard.ta.align(lv.ALIGN.TOP_MID, 0, 170)
        self.keyboard.update_count_tips()

        self.nav_back.add_event_cb(self.on_cancel, lv.EVENT.CLICKED, None)

    def on_ready(self, event_obj):
        input_text = self.keyboard.ta.get_text()
        self.channel.publish(input_text)
        self.keyboard.ta.set_text("")
        self.destroy(200)

    def on_cancel(self, event_obj):
        target = event_obj.get_target()
        if target == self.nav_back.nav_btn:
            self.channel.publish(None)
            self.destroy(200)

    # def on_rti_scan(self, event_obj):
    #     had_focus = self.keyboard.ta.has_state(lv.STATE.FOCUSED)
    #     if had_focus:
    #         self.keyboard.ta.clear_state(lv.STATE.FOCUSED)
    #     self.add_flag(lv.obj.FLAG.HIDDEN)
    #     scan_screen = InputTiSerialScan()

    #     async def update_keyboard():
    #         qr_data = None
    #         try:
    #             qr_data = await scan_screen.request()
    #             if qr_data:
    #                 self.keyboard.ta.set_text(qr_data)
    #                 self.keyboard.ta.set_cursor_pos(lv.TEXTAREA_CURSOR.LAST)
    #                 self.keyboard.update_ok_button_state()
    #                 self.keyboard.update_count_tips()
    #             await loop.sleep(20)
    #         finally:
    #             self.clear_flag(lv.obj.FLAG.HIDDEN)
    #             if had_focus and not qr_data:
    #                 self.keyboard.ta.add_state(lv.STATE.FOCUSED)

    #     workflow.spawn(update_keyboard())


class InputTiCodeConfirm(AnimScreen):
    CODE_LEN = 4
    CELL_SIZE = 100
    CELL_GAP = 17

    def __init__(self, prev_scr=None, idx: int = 0):
        super().__init__(
            title=_(i18n_keys.TITLE__TI_VERIFY_DIGITAL_ENCODING),
            prev_scr=prev_scr,
            nav_back=True,
        )

        self.title.align(lv.ALIGN.TOP_MID, 0, 50)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)

        self.keyboard = NumberKeyboard(
            self, max_len=self.CODE_LEN, min_len=self.CODE_LEN, hide_ta=True
        )
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)

        self.keyboard.ta.add_flag(lv.obj.FLAG.HIDDEN)
        self.keyboard.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)

        total_width = (
            self.CODE_LEN * self.CELL_SIZE + (self.CODE_LEN - 1) * self.CELL_GAP
        )
        start_x = -(total_width // 2) + self.CELL_SIZE // 2

        idx_lbl = lv.label(self)
        idx_lbl.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.INPUT_TIP_FG)
            .text_align_center(),
            0,
        )
        idx_lbl.set_text(f"{idx:02d}")
        idx_lbl.align(lv.ALIGN.TOP_MID, 0, 130)
        self.code_cells = []
        for i in range(self.CODE_LEN):
            cell = lv.obj(self)
            cell.set_size(self.CELL_SIZE, self.CELL_SIZE)
            cell.add_style(
                StyleWrapper()
                .radius(16)
                .bg_color(lv_theme.KEYBOARD_KEY_BG)
                .bg_opa(lv.OPA.COVER)
                .border_width(0)
                .pad_all(0),
                0,
            )
            x_offset = start_x + i * (self.CELL_SIZE + self.CELL_GAP)
            cell.align_to(idx_lbl, lv.ALIGN.OUT_BOTTOM_MID, x_offset, 20)

            lbl = lv.label(cell)
            lbl.add_style(
                StyleWrapper()
                .text_font(font_GeistSemiBold48)
                .text_color(lv_theme.KEYBOARD_KEY_FG)
                .text_align_center(),
                0,
            )
            lbl.set_text("")
            lbl.center()
            self.code_cells.append((cell, lbl))

        self.input_result = None

    def _update_cells(self):
        text = self.keyboard.ta.get_text()
        for i, (_cell, lbl) in enumerate(self.code_cells):
            if i < len(text):
                lbl.set_text(text[i])
            else:
                lbl.set_text("")

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            self._update_cells()
            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if len(input) < self.CODE_LEN:
                return
            self.input_result = input
            self.channel.publish(self.input_result)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.load_screen(self.prev_scr, destroy_self=True)

    def cb_nva_back_event(self):
        self.channel.publish(0)
        if self.prev_scr is not None:
            self.load_screen(self.prev_scr, destroy_self=True)


class InputLitePinConfirm(FullSizeWindow):
    def __init__(self, title):
        super().__init__(
            title=title,
            subtitle=None,
            anim_dir=0,
        )
        self.title.text.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_align_center()
            .text_letter_space(0),
            0,
        )
        self.title.align(lv.ALIGN.TOP_MID, 0, 0)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = NumberKeyboard(self, max_len=6, min_len=6)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)
        self.input_result = None

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if len(input) < 6:
                return
            self.input_result = input
            self.channel.publish(self.input_result)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.destroy()


async def pin_mismatch(ctx) -> None:
    from trezor.ui.layouts import show_warning

    is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
    await show_warning(
        ctx=ctx,
        br_type="pin_not_match",
        header=_(i18n_keys.TITLE__NOT_MATCH),
        content=_(
            i18n_keys.CONTENT__THE_TWO_UKEY_LITE_USED_FOR_CONNECTION_ARE_NOT_THE_SAME
            if is_lite
            else i18n_keys.CONTENT__THE_TWO_UKEY_RING_USED_FOR_CONNECTION_ARE_NOT_THE_SAME
        ),
        # icon=theme_path_default("success.png"),
        icon=theme_path_png("danger"),
        btn_yes_bg_color=lv_theme.BTN_YES_BG,
    )


async def request_lite_pin(ctx, prompt: str) -> str:
    pin_screen = InputLitePinConfirm(prompt)
    pin = await ctx.wait(pin_screen.request())
    return pin


async def request_existing_lite_pin(ctx, subtitle: str = "") -> str:
    pin_screen = InputLitePin(subtitle=subtitle)
    pin = await ctx.wait(pin_screen.request())
    return pin


async def request_lite_pin_confirm(ctx, first_title: str | None = None) -> str:
    while True:
        is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
        pin1 = await request_lite_pin(
            ctx,
            first_title
            or _(
                i18n_keys.TITLE__ENTER_UKEY_LITE_PIN
                if is_lite
                else i18n_keys.TITLE__ENTER_UKEY_RING_PIN
            ),
        )
        if pin1 == 0:
            return pin1
        pin2 = await request_lite_pin(
            ctx,
            _(
                i18n_keys.TITLE__CONFIRM_UKEY_LITE_PIN
                if is_lite
                else i18n_keys.TITLE__CONFIRM_UKEY_RING_PIN
            ),
        )
        if pin2 == 0:
            return pin2
        if pin1 == pin2:
            return pin1
        await pin_mismatch(ctx)


class SetupComplete(FullSizeWindow):
    def __init__(self, subtitle=""):
        super().__init__(
            title=_(i18n_keys.TITLE__WALLET_IS_READY),
            subtitle=subtitle,
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            icon_path=theme_path_png("hidden-wallet"),
            anim_dir=0,
        )

    def eventhandler(self, event_obj: lv.event_t):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.btn_yes:
                self.channel.publish(1)
                self.destroy()
                lv.scr_act().del_delayed(500)
                from apps.base import set_homescreen

                set_homescreen()
            elif target in (self.nav_back, self.nav_back.nav_btn):
                self.show_dismiss_anim()
                self.channel.publish(0)


class InputPassphrasePinConfirm(FullSizeWindow):
    def __init__(self, title, original_input=None):
        super().__init__(
            title=title,
            subtitle=None,
            anim_dir=0,
        )
        self.title.text.add_style(StyleWrapper().text_align_center(), 0)
        self.title.align(lv.ALIGN.TOP_MID, 0, 24)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = NumberKeyboard(self, max_len=50, min_len=6)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)
        self.input_result = None

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if len(input) < 6:
                return
            self.input_result = input
            self.channel.publish(self.input_result)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.destroy()


async def request_passphrase_pin(ctx, prompt: str) -> str:
    pin_screen = InputPassphrasePinConfirm(prompt)
    pin = await ctx.wait(pin_screen.request())
    return pin


async def request_passphrase_pin_confirm(ctx) -> str:
    while True:
        pin1 = await request_passphrase_pin(
            ctx, _(i18n_keys.PASSPHRASE__SET_PASSPHRASE_PIN)
        )
        if pin1 == 0:
            return pin1

        pin2 = await request_passphrase_pin(ctx, _(i18n_keys.TITLE__ENTER_PIN_AGAIN))
        if pin2 == 0:
            return pin2
        if pin1 == pin2:
            return pin1
        await passphrase_pin_mismatch(ctx)


async def passphrase_pin_mismatch(ctx) -> None:
    from trezor.ui.layouts import show_warning

    await show_warning(
        ctx=ctx,
        br_type="pin_not_match",
        header=_(i18n_keys.TITLE__NOT_MATCH),
        content=_(i18n_keys.SUBTITLE__SETUP_SET_PIN_PIN_NOT_MATCH),
        # icon=theme_path_default("success.png"),
        icon=theme_path_png("success"),
        btn_yes_bg_color=lv_theme.BTN_YES_BG,
    )


async def request_change_passphrase_pin(ctx) -> str:
    while True:
        pin1 = await request_passphrase_pin(ctx, _(i18n_keys.TITLE__ENTER_NEW_PIN))
        if pin1 == 0:
            return pin1

        pin2 = await request_passphrase_pin(ctx, _(i18n_keys.TITLE__ENTER_PIN_AGAIN))
        if pin2 == 0:
            return pin2
        if pin1 == pin2:
            return pin1
        await passphrase_pin_mismatch(ctx)


class InputMainPin(FullSizeWindow):
    def __init__(self):
        super().__init__(
            title=_(i18n_keys.TITLE__ENTER_PIN),
            subtitle=_(i18n_keys.CONTENT__PIN_FOR_STANDARD_WALLET),
            anim_dir=0,
        )
        self.title.text.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_align_center()
            .text_letter_space(0),
            0,
        )
        self.title.align(lv.ALIGN.TOP_MID, 0, 24)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.keyboard = NumberKeyboard(self, max_len=50, min_len=4)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.CANCEL, None)
        self.keyboard.add_event_cb(self.on_event, lv.EVENT.VALUE_CHANGED, None)

    def on_event(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            return
        elif code == lv.EVENT.READY:
            input = self.keyboard.ta.get_text()
            if len(input) < 6:
                return
            self.channel.publish(input)
        elif code == lv.EVENT.CANCEL:
            self.channel.publish(0)

        self.clean()
        self.destroy()
