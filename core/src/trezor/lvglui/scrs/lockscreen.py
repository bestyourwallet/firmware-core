import storage.device as storage_device
from trezor import ui, utils
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import StatusBar
from . import font_GeistRegular26, lv_theme, theme_path_png
from .common import Screen, lv
from .components.doubleclick import DoubleClickDetector
from .widgets.style import StyleWrapper

ANIM_TIME = 20
ANIM_PLAYBACK_TIME = 20
ANIM_PLAYBACK_DELAY = 5


def format_lockscreen_ble_name(ble_name: str | None = None) -> str:
    if not ble_name:
        from trezor import uart

        ble_name = storage_device.get_ble_name() or uart.get_ble_name()
    return ble_name.split()[-1] if ble_name else ""


class LockScreen(Screen):
    @classmethod
    def retrieval(cls) -> tuple[bool, "LockScreen" | None]:
        try:
            if __debug__:
                print(
                    f"[LOCKSCREEN] retrieval() - checking _instance: {hasattr(cls, '_instance')}"
                )
            if hasattr(cls, "_instance") and cls._instance.is_visible():
                if __debug__:
                    print(
                        "[LOCKSCREEN] retrieval() - _instance is visible, returning True"
                    )
                return True, cls._instance
        except Exception:
            pass
        return False, None

    def __init__(self, device_name, ble_name="", dev_state=None):
        lockscreen = storage_device.get_homescreen()
        if isinstance(lockscreen, tuple):
            lockscreen = lockscreen[0]
        ble_name = format_lockscreen_ble_name(ble_name)
        self.double_click = DoubleClickDetector(click_timeout=800, click_dist=50)
        if not hasattr(self, "_init"):
            self._init = True
            self._unlock_task = None
            super().__init__(title=device_name, subtitle=ble_name)
            self.title.text.add_style(
                StyleWrapper().text_align_center().text_color(lv_theme.DTL_TITLE_FG),
                0,
            )
            self.title.text.set_style_min_height(56, 0)
            self.subtitle.add_style(
                StyleWrapper().text_align_center().text_color(lv_theme.DTL_SUBTITLE_FG),
                0,
            )
        else:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.DTL_BG).bg_img_src(lockscreen),
                0,
            )
            self.subtitle.set_text(ble_name)
            self.show_tips()
            self.update_title()
            return
        self.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.title.align_to(self.content_area, lv.ALIGN.TOP_MID, 0, 108)
        self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 12)
        self.add_style(
            StyleWrapper().bg_color(lv_theme.DTL_BG).bg_img_src(lockscreen),
            0,
        )
        self.tap_tip = lv.label(self.content_area)
        self.tap_tip.set_long_mode(lv.label.LONG.WRAP)

        self.show_tips()
        self.up_arrow = lv.img(self.content_area)
        self.up_arrow.set_src(theme_path_png("arrow_up_3"))
        # self.up_arrow.set_style_img_opa(int(lv.OPA.COVER * 0.25), 0)
        self.up_arrow.align_to(self.tap_tip, lv.ALIGN.OUT_TOP_MID, 0, -18)

        self.lock_state = lv.img(self.content_area)
        self.lock_state.set_src(theme_path_png("lock"))
        # self.lock_state.set_style_img_opa(int(lv.OPA.COVER * 0.25), 0)
        self.lock_state.align_to(self.up_arrow, lv.ALIGN.OUT_TOP_MID, 0, -76)
        self.add_event_cb(self.on_slide_up, lv.EVENT.GESTURE, None)
        StatusBar.get_instance().set_style_bg_opa(lv.OPA.TRANSP, 0)
        self.update_title()

    def update_title(self):
        if not storage_device.is_lockscreen_show_model_name():
            self.title.add_flag(lv.obj.FLAG.HIDDEN)
        elif self.title.has_flag(lv.obj.FLAG.HIDDEN):
            self.title.clear_flag(lv.obj.FLAG.HIDDEN)
        if not storage_device.is_lockscreen_show_ble_id():
            self.subtitle.add_flag(lv.obj.FLAG.HIDDEN)
        elif self.subtitle.has_flag(lv.obj.FLAG.HIDDEN):
            self.subtitle.clear_flag(lv.obj.FLAG.HIDDEN)

    def show_tips(self, level: int = 0):
        if level:
            if level == 1:
                text = _(i18n_keys.MSG__FINGERPRINT_NOT_RECOGNIZED_TRY_AGAIN)
                self.tap_tip.set_text(text)
                if __debug__:
                    print(f"[LOCKSCREEN] Set text for level 1: {text}")
            elif level == 2:
                text = _(
                    i18n_keys.MSG__YOUR_PIN_CODE_REQUIRED_TO_ENABLE_FINGERPRINT_UNLOCK
                )
                self.tap_tip.set_text(text)
                if __debug__:
                    print(f"[LOCKSCREEN] Set text for level 2: {text}")
            elif level == 3:
                text = _(i18n_keys.MSG__PUT_FINGER_ON_THE_FINGERPRINT)
                self.tap_tip.set_text(text)
                if __debug__:
                    print(f"[LOCKSCREEN] Set text for level 3: {text}")
            elif level == 4:
                text = _(i18n_keys.MSG__CLEAN_FINGERPRINT_SENSOR_AND_TRY_AGAIN)
                self.tap_tip.set_text(text)
                if __debug__:
                    print(f"[LOCKSCREEN] Set text for level 4: {text}")
        else:
            # if fingerprints.is_available():
            #     self.tap_tip.set_text(
            #         _(i18n_keys.MSG__USE_FINGERPRINT_OR_TAP_TO_UNLOCK)
            #     )
            # self._show_fingerprint_prompt_if_necessary()
            # else:
            self.tap_tip.set_text(_(i18n_keys.LOCKED_TEXT__TAP_TO_UNLOCK))

        self.tap_tip.set_size(450, lv.SIZE.CONTENT)
        self.tap_tip.align(lv.ALIGN.BOTTOM_MID, 0, -44)
        self.tap_tip.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular26)
            .text_letter_space(-1)
            .max_width(450)
            .text_align_center()
            .text_color(lv_theme.DTL_BTIP_FG),
            0,
        )
        if hasattr(self, "up_arrow"):
            if level:
                self.up_arrow.add_flag(lv.obj.FLAG.HIDDEN)
            else:
                self.up_arrow.clear_flag(lv.obj.FLAG.HIDDEN)
                self.up_arrow.align_to(self.tap_tip, lv.ALIGN.OUT_TOP_MID, 0, -18)
        if hasattr(self, "lock_state"):
            if level:
                self.lock_state.align_to(self.tap_tip, lv.ALIGN.OUT_TOP_MID, 0, -16)
            elif hasattr(self, "up_arrow"):
                self.lock_state.align_to(self.up_arrow, lv.ALIGN.OUT_TOP_MID, 0, -76)

    def show_finger_mismatch_anim(self):
        if __debug__:
            print("[LOCKSCREEN] show_finger_mismatch_anim called")
        self.anim_right = lv.anim_t()
        self.anim_right.init()
        self.anim_right.set_var(self.lock_state)
        self.anim_right.set_values(220, 230)
        self.anim_right.set_time(ANIM_TIME)
        self.anim_right.set_playback_delay(ANIM_PLAYBACK_DELAY)
        self.anim_right.set_playback_time(ANIM_PLAYBACK_TIME)
        self.anim_right.set_repeat_delay(5)
        self.anim_right.set_repeat_count(1)
        self.anim_right.set_path_cb(lv.anim_t.path_ease_in)
        self.anim_right.set_custom_exec_cb(lambda _a, val: self.anim_set_x(val))

        self.anim_left = lv.anim_t()
        self.anim_left.init()
        self.anim_left.set_var(self.lock_state)
        self.anim_left.set_values(220, 210)
        self.anim_left.set_time(ANIM_TIME)
        self.anim_left.set_playback_delay(ANIM_PLAYBACK_DELAY)
        self.anim_left.set_playback_time(ANIM_PLAYBACK_TIME)
        self.anim_left.set_repeat_delay(5)
        self.anim_left.set_repeat_count(1)
        self.anim_left.set_path_cb(lv.anim_t.path_ease_in)
        self.anim_left.set_custom_exec_cb(lambda _a, val: self.anim_set_x(val))
        self.anim_left.set_deleted_cb(lambda _a: lv.anim_t.start(self.anim_right))

        lv.anim_t.start(self.anim_left)

    def anim_set_x(self, x):
        try:
            self.lock_state.set_x(x)
        except Exception:
            pass

    # def _show_fingerprint_prompt_if_necessary(self):
    #     if storage_device.has_prompted_fingerprint():
    #         if hasattr(self, "fingerprint_prompt"):
    #             self.fingerprint_prompt.delete()
    #         return
    #     self.fingerprint_prompt = lv.img(self.content_area)
    #     self.fingerprint_prompt.set_src(theme_path_default("prompt_fingerprint-prompt.png"))
    #     self.fingerprint_prompt.set_pos(424, 28)
    #     storage_device.set_fingerprint_prompted()

    async def _unlock(self):
        from apps.base import unlock_device
        from .pinscreen import InputPin

        try:
            await unlock_device(into_optscreen=True)
        finally:
            InputPin.clear_pending_fingerprint_subtitle()
            self._unlock_task = None

    def request_unlock(self, fingerprint_subtitle: str = ""):
        from trezor import workflow
        from .pinscreen import InputPin

        if fingerprint_subtitle:
            InputPin.set_fingerprint_subtitle(fingerprint_subtitle)
        if self._unlock_task is not None and not self._unlock_task.finished:
            return
        self._unlock_task = workflow.spawn(self._unlock())

    def eventhandler(self, event_obj: lv.event_t):
        code = event_obj.code
        if code == lv.EVENT.CLICKED:
            if self.channel.takers:
                self.channel.publish("clicked")
            else:
                if not ui.display.backlight():
                    if not storage_device.is_tap_awake_enabled():
                        return
                    else:
                        indev = lv.indev_get_act()
                        point = lv.point_t()
                        indev.get_point(point)
                        is_double = self.double_click.handle_click(point)
                        if not is_double:
                            return

                if utils.turn_on_lcd_if_possible():
                    return
                self.request_unlock()
                import storage.cache

                storage.cache.start_session()

    def on_slide_up(self, event_obj: lv.event_t):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.TOP:
                if not ui.display.backlight():
                    return
                self.request_unlock()

    def _load_scr(self, scr: "Screen", back: bool = False) -> None:
        lv.scr_load(scr)
