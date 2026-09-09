import storage.device
from trezor import utils, workflow
from trezor.langs import langs_keys, langs_values
from trezor.lvglui.i18n import gettext as _, i18n_refresh, keys as i18n_keys
from trezor.messages import RecoveryDevice, ResetDevice
from trezor.wire import DUMMY_CONTEXT

from apps.management.recovery_device import recovery_device
from apps.management.reset_device import reset_device

from . import font_GeistMono28, lv_theme, theme_path_png
from .common import FullSizeWindow, Screen, lv  # noqa: F401,F403,F405
from .components.container import ContainerFlexCol
from .components.qrcode import QRCode
from .components.radio import RadioTrigger
from .widgets.style import StyleWrapper

word_cnt_strength_map = {
    12: 128,
    18: 192,
    24: 256,
}

language = "en"

INIT_IDLE_SCREEN_OFF_MS = 60 * 1000  # * 60
INIT_SCREEN_OFF_POWER_OFF_MS = 10 * 60 * 1000  # * 60

_INIT_IDLE_ACTIVITY_EVENTS = (
    lv.EVENT.PRESSED,
    lv.EVENT.PRESSING,
    lv.EVENT.RELEASED,
    lv.EVENT.CLICKED,
    lv.EVENT.GESTURE,
    lv.EVENT.VALUE_CHANGED,
    lv.EVENT.KEY,
    lv.EVENT.SCROLL,
)


class InitIdleScreenOff:
    ACTIVITY_EVENTS = _INIT_IDLE_ACTIVITY_EVENTS

    def __init__(self, screen) -> None:
        self._screen = screen
        self._destroyed = True
        self._cb_registered = False
        self._restart_on_activity = False
        self._timer = None
        self._power_off_task = None

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    def start(self) -> None:
        self._destroyed = False
        self._restart_on_activity = False
        self._stop_power_off_task()
        self._register_activity_handlers()
        if self._timer is not None:
            try:
                self._timer._del()
            except Exception:
                pass
        self._timer = lv.timer_create(
            self._screen_off_cb, INIT_IDLE_SCREEN_OFF_MS, None
        )

    def reset(self) -> None:
        if self._destroyed:
            return
        if self._timer is not None:
            self._timer.reset()
        else:
            self.start()

    def stop(self, restart_on_activity: bool = False) -> None:
        self._destroyed = True
        self._restart_on_activity = restart_on_activity
        timer = self._timer
        self._timer = None
        if restart_on_activity:
            self._start_power_off_task()
        else:
            self._stop_power_off_task()
        if timer is None:
            return
        try:
            timer._del()
        except Exception as e:
            if __debug__:
                print(f"Error deleting init idle screen off timer: {e}")

    def _register_activity_handlers(self) -> None:
        if self._cb_registered:
            return

        def _on_activity(event_obj) -> None:
            if event_obj.code not in self.ACTIVITY_EVENTS:
                return
            if self._destroyed:
                if self._restart_on_activity:
                    from trezor.ui import display

                    if display.backlight():
                        if __debug__:
                            print("InitIdleScreenOff: resumed by activity")
                        self.start()
                return
            else:
                self.reset()

        for code in self.ACTIVITY_EVENTS:
            self._screen.add_event_cb(_on_activity, code, None)
        self._cb_registered = True

    def _start_power_off_task(self) -> None:
        if self._power_off_task is not None:
            return

        async def _power_off_delay():
            from trezor import loop

            if __debug__:
                print("InitIdleScreenOff: power off delay start")
            await loop.sleep(INIT_SCREEN_OFF_POWER_OFF_MS)
            if __debug__:
                print(
                    "InitIdleScreenOff: power off delay fired",
                    "restart_on_activity",
                    self._restart_on_activity,
                    "destroyed",
                    self._destroyed,
                )
            self._power_off_task = None
            if self._restart_on_activity and self._destroyed:
                self._restart_on_activity = False
                self._power_off()
            elif __debug__:
                print(
                    "InitIdleScreenOff: skip power off, screen was resumed or stopped"
                )

        from trezor import loop

        self._power_off_task = loop.spawn(_power_off_delay())

    def _stop_power_off_task(self) -> None:
        task = self._power_off_task
        self._power_off_task = None
        if task is None:
            return
        try:
            task.close()
        except Exception as e:
            if __debug__:
                print(f"Error closing init screen off power off task: {e}")

    def _screen_off_cb(self, _timer) -> None:
        if self._destroyed:
            return
        if __debug__:
            print("InitIdleScreenOff: screen off timeout fired")
        self.stop(restart_on_activity=True)
        self._screen_off()

    @staticmethod
    def _screen_off() -> None:
        from trezor.ui import display

        if __debug__:
            print("InitIdleScreenOff: display backlight off")
        display.backlight(0)

    @staticmethod
    def _power_off() -> None:
        from trezor.ui import display

        if __debug__:
            print(
                "InitIdleScreenOff: power off requested",
                "charging",
                utils.CHARGING,
                "backlight",
                display.backlight(),
            )
        if utils.CHARGING and __debug__:
            print("InitIdleScreenOff: charging true, still show shutdown screen")

        from .homescreen import ShutingDown

        if __debug__:
            print("InitIdleScreenOff: show ShutingDown screen")
        ShutingDown(_(i18n_keys.TITLE__SHUTDOWN))


class InitScreen(Screen):
    def _setup_poweroff_btn(self) -> None:
        if getattr(self, "rti_btn", None) is not None:
            return
        self.rti_btn = lv.imgbtn(self.content_area)
        self.rti_btn.set_size(48, 48)
        self.rti_btn.set_ext_click_area(100)
        self.rti_btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.rti_btn.set_style_bg_img_src(theme_path_png("poweroff-40"), 0)
        self.rti_btn.align(lv.ALIGN.TOP_RIGHT, -12, 56)
        self.rti_btn.move_foreground()

    def load_screen(self, scr, destroy_self: bool = False):
        if getattr(self, "_defer_load", False):
            return
        super().load_screen(scr, destroy_self)

    def __init__(self):
        if not hasattr(self, "_init"):
            self._defer_load = True
            super().__init__(title=_(i18n_keys.TITLE__LANGUAGE))
            self._defer_load = False
            self.title.text.add_style(StyleWrapper().text_align_left(), 0)
            self.container = ContainerFlexCol(
                self.content_area, self.title, padding_row=2, pos=(0, 20)
            )
            self.choices = RadioTrigger(
                self.container,
                langs_values,
                bg_color=lv_theme.CONT_BG,
                item_bg_color=lv_theme.CONT_ITEM_BG,
                inteval_line=True,
            )
            self._setup_poweroff_btn()
            self.container.add_event_cb(self.on_ready, lv.EVENT.READY, None)
            self.load_screen(self)
            self._idle_screen_off = InitIdleScreenOff(self)
            self._idle_screen_off.start()
            self._init = True
        else:
            self.title.set_text(_(i18n_keys.TITLE__LANGUAGE))
            if self._idle_screen_off.destroyed:
                self._idle_screen_off.start()
            else:
                self._idle_screen_off.reset()
            return

        # pressed_style = (
        #     StyleWrapper()
        #     .bg_color(lv_theme.BTN_YES_BG)
        #     .transform_height(-2)
        #     .transition(DefaultTransition())
        # )
        # self.crt_btn = NormalButton(
        #     self.content_area,
        #     _(i18n_keys.CONTENT__CERTIFICATIONS),
        #     pressed_style=pressed_style,
        # )
        # self.crt_btn.add_style(
        #     StyleWrapper()
        #     .text_font(font_GeistRegular30)
        #     .bg_color(lv_theme.BTN_YES_BG)
        #     .text_color(lv_theme.BTN_YES_FG),
        #     0,
        # )
        # # self.crt_btn.enable_no_bg_mode(skip_pressed_style=True)
        # self.crt_btn.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)
        # self.crt_btn.add_event_cb(self.on_crt_btn, lv.EVENT.CLICKED, None)

    def on_click_ext(self, target):
        self._idle_screen_off.reset()
        from .homescreen import PowerOff

        PowerOff()

    def on_ready(self, _event_obj):
        global language
        language = langs_keys[self.choices.get_selected_index()]
        i18n_refresh(language)
        self._idle_screen_off.stop()
        VerifyActivateDevice()

    # def on_crt_btn(self, _event_obj):
    #     from .template import CertificationInfo
    #     CertificationInfo()

    def _load_scr(self, scr: "Screen", back: bool = False) -> None:
        lv.scr_load(scr)


class VerifyActivateDevice(FullSizeWindow):
    SHOW_TIME = 10

    def __init__(self):
        super().__init__(
            title=_(i18n_keys.TITLE__VERIFY_ACTIVATE_DEVICE),
            subtitle=_(i18n_keys.SUBTITLE__VERIFY_ACTIVATE_DEVICE),
            confirm_text=_(i18n_keys.BUTTON__VEIRIFY_DEVICE),  # cancel_text
            cancel_text=_(i18n_keys.BUTTON__SKIP_WITH_TIME).format(
                VerifyActivateDevice.SHOW_TIME
            ),
            button_layout=0,
        )
        self.btn_no.disable(
            bg_color=lv_theme.BTN_CANCEL_DBG, text_color=lv_theme.BTN_CANCEL_DFG
        )
        self.time_left = VerifyActivateDevice.SHOW_TIME
        self._destroyed = False
        self.timer = lv.timer_create(self.timer_cb, 1000, None)
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self._idle_screen_off = InitIdleScreenOff(self)
        self._idle_screen_off.start()

    def _stop_timer(self):
        timer = getattr(self, "timer", None)
        if timer is None:
            return
        self.timer = None
        try:
            timer._del()
        except Exception as e:
            if __debug__:
                print(f"Error deleting verify activation timer: {e}")

    def destroy(self, delay_ms=400):
        self._destroyed = True
        self._stop_timer()
        self._idle_screen_off.stop()
        super().destroy(delay_ms)

    def timer_cb(self, timer):
        if self._destroyed or self.timer is None:
            return
        self.time_left -= 1
        try:
            if self.btn_no and hasattr(self.btn_no, "label") and self.btn_no.label:
                self.btn_no.label.set_text(
                    _(i18n_keys.BUTTON__SKIP_WITH_TIME).format(self.time_left)
                )
        except Exception as e:
            if __debug__:
                print(f"Error updating timer button: {e}")
            self._stop_timer()
            return
        if self.time_left == 0:
            self._stop_timer()
            self.btn_no.label.set_text(_(i18n_keys.BUTTON__SKIP))
            self.btn_no.enable(
                bg_color=lv_theme.BTN_CANCEL_BG, text_color=lv_theme.BTN_CANCEL_FG
            )
            # lv.event_send(self.btn_no, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                self._idle_screen_off.start()
                return
            if target == self.btn_no:
                self._stop_timer()
                QuickStart()
                self.destroy(0)
            elif target == self.btn_yes:
                self._stop_timer()
                self._idle_screen_off.stop()
                self.btn_no.enable(
                    bg_color=lv_theme.BTN_CANCEL_BG, text_color=lv_theme.BTN_CANCEL_FG
                )
                self.btn_no.label.set_text(_(i18n_keys.BUTTON__SKIP))
                DeviceSerialDisplay()
            elif target in (self.nav_back, self.nav_back.nav_btn):
                self._stop_timer()
                self.show_dismiss_anim()
                self.channel.publish(0)


class DeviceSerialDisplay(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__DEVICE_SERIAL_NUMBER),
            None,
            cancel_text="",
            icon_path=theme_path_png("device_serial"),
            anim_dir=0,
        )

        self.icon.align(lv.ALIGN.TOP_MID, 0, 0)
        self.title.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)
        self.panel = lv.obj(self.content_area)
        self.panel.set_size(450, 80)
        self.panel.add_style(
            StyleWrapper().bg_color(lv_theme.INPUT_BG).radius(10).border_width(0),
            0,
        )
        self.panel.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.panel.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 40)
        serial_code = storage.device.get_serial()
        self.serial_code = lv.label(self.panel)
        self.serial_code.set_long_mode(lv.label.LONG.WRAP)
        self.serial_code.set_style_text_letter_space(
            -2, lv.PART.MAIN | lv.STATE.DEFAULT
        )
        self.serial_code.set_text(serial_code)
        self.serial_code.add_style(
            StyleWrapper().text_font(font_GeistMono28).text_color(lv_theme.INPUT_WFG), 0
        )
        self.serial_code.align(lv.ALIGN.CENTER, 0, 0)
        self.qr = QRCode(
            self.content_area, f"https://ukey.com/hw-verify?sn={serial_code}", size=200
        )
        # self.qr = lv.obj(self.content_area)
        # self.qr.set_size(200,200)

        self.qr.align_to(self.panel, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
        self.qr_tip = lv.label(self.content_area)
        self.qr_tip.set_text(_(i18n_keys.SUBTITLE__DEVICE_SERIAL_NUMBER))
        self.qr_tip.set_long_mode(lv.label.LONG.WRAP)
        self.qr_tip.set_size(450, lv.SIZE.CONTENT)
        self.qr_tip.add_style(
            StyleWrapper()
            .text_color(lv_theme.DT_TITLE_TIP_FG)
            .text_font(font_GeistMono28)
            .text_align_center()
            .pad_bottom(15),
            0,
        )
        self.qr_tip.align_to(self.qr, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)
        # self.btn_no.enable()
        self.destroyed = False
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self._idle_screen_off = InitIdleScreenOff(self)
        self._idle_screen_off.start()

    def destroy(self, delay_ms=400):
        self.destroyed = True
        self._idle_screen_off.stop()
        super().destroy(delay_ms)

    # trezor.lvglui.scrs
    # from .homescreen import ScanScreen
    # ScanScreen.notify_close()


class QuickStart(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__QUICK_START),
            _(i18n_keys.SUBTITLE__SETUP_QUICK_START),
            confirm_text=_(i18n_keys.BUTTON__CREATE_NEW_WALLET),
            cancel_text=_(i18n_keys.BUTTON__IMPORT_WALLET),
            anim_dir=0,
            bg_color=lv_theme.DT_BG,
            button_layout=0,
        )
        self.add_nav_back()
        self.btn_layout_ver()
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)
        # self.content_area.set_style_min_height(730, 0)
        self.update_btn_layout()
        # self.content_area.set_style_bg_color(lv_colors.UKEY_GRAY_3, 0)
        # self.content_area.set_style_bg_opa(lv.OPA.COVER, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, -190)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if target == self.btn_yes:
                workflow.spawn(
                    reset_device(
                        DUMMY_CONTEXT,
                        ResetDevice(
                            strength=128,
                            language=language,
                            pin_protection=True,
                        ),
                    ),
                )
            elif target == self.btn_no:
                SelectImportType()

            elif target in (self.nav_back, self.nav_back.nav_btn):
                self.show_dismiss_anim()
                self.channel.publish(0)
            else:
                return
            self.destroy(100)


class SelectImportType(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__IMPORT_WALLET),
            _(i18n_keys.CONTENT__SELECT_THE_WAY_YOU_WANT_TO_IMPORT),
            anim_dir=0,
        )
        # self.add_nav_back()
        self.choices = RadioTrigger(
            self,
            f"{_(i18n_keys.OPTIONS_RECOVERY_PHRASE)}\nUKey Seed Card\nUKey Seed Ti\nUKey Seed Ring",
            item_padding=20,
            item_radius=20,
            radius=20,
            bg_color=None,
            item_center=True,
            inteval_line=False,
        )
        self.add_event_cb(self.on_ready, lv.EVENT.READY, None)
        # self.add_event_cb(self.on_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.gesture_handler, lv.EVENT.GESTURE, None)

    def gesture_handler(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def on_ready(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
        self.show_dismiss_anim()
        selected_index = self.choices.get_selected_index()
        if selected_index == 0:
            workflow.spawn(
                recovery_device(
                    DUMMY_CONTEXT,
                    RecoveryDevice(
                        enforce_wordlist=True,
                        language=language,
                        pin_protection=True,
                    ),
                    "phrase",
                )
            )
        elif selected_index == 1:
            workflow.spawn(
                recovery_device(
                    DUMMY_CONTEXT,
                    RecoveryDevice(
                        enforce_wordlist=True,
                        language=language,
                        pin_protection=True,
                    ),
                    "lite",
                )
            )
        elif selected_index == 2:
            workflow.spawn(
                recovery_device(
                    DUMMY_CONTEXT,
                    RecoveryDevice(
                        enforce_wordlist=True,
                        language=language,
                        pin_protection=True,
                    ),
                    "ti",
                )
            )
        elif selected_index == 3:
            workflow.spawn(
                recovery_device(
                    DUMMY_CONTEXT,
                    RecoveryDevice(
                        enforce_wordlist=True,
                        language=language,
                        pin_protection=True,
                    ),
                    "ring",
                )
            )

    # def on_back(self, event_obj):
    #     target = event_obj.get_target()
    #     if target == self.nav_back.nav_btn:
    #         self.channel.publish(0)
    #         self.show_dismiss_anim()
