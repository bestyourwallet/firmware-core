from trezor import ui
from trezor.lvglui import StatusBar, get_elapsed
from trezor.lvglui.scrs import lv, theme_path_png
from trezor.lvglui.scrs.widgets.style import StyleWrapper

from . import lv_theme


class ChargingPromptScr(lv.obj):
    _instance = None
    AUTO_CLOSE_MS = 1000

    @classmethod
    def get_instance(cls) -> "ChargingPromptScr":
        if cls._instance is None:
            cls._instance = ChargingPromptScr()
        else:
            cls._instance._reset_auto_close_timer()
        return cls._instance

    @classmethod
    def has_instance(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def __init__(self) -> None:
        super().__init__(lv.layer_top())
        self._pause_camera_refresh()
        self.set_size(lv.pct(100), lv.pct(100))
        self.align(lv.ALIGN.TOP_LEFT, 0, 0)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.DT_BG)
            .bg_opa(lv.OPA.COVER)
            .pad_all(0)
            .border_width(0)
            .radius(0),
            lv.PART.MAIN | lv.STATE.DEFAULT,
        )
        self.charging_bg = lv.img(self)
        self.charging_bg.set_src(theme_path_png("charging-battery"))
        self.charging_bg.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
        self.charging_bg.align(lv.ALIGN.TOP_MID, 0, 300)

        StatusBar.get_instance().move_foreground()

        self._destroyed = False
        self.auto_close_timer = None
        self._start_auto_close_timer()

    def _pause_camera_refresh(self) -> None:
        self._camera_refresh_paused = False
        try:
            from trezor.qr import pause_camera_refresh

            pause_camera_refresh()
            self._camera_refresh_paused = True
        except Exception as e:
            if __debug__:
                print(f"Error pausing camera refresh for charging prompt: {e}")

    def _resume_camera_refresh(self) -> None:
        if not getattr(self, "_camera_refresh_paused", False):
            return
        self._camera_refresh_paused = False
        try:
            from trezor.qr import resume_camera_refresh

            resume_camera_refresh()
        except Exception as e:
            if __debug__:
                print(f"Error resuming camera refresh for charging prompt: {e}")

    def _start_auto_close_timer(self) -> None:
        self._stop_auto_close_timer()
        self.auto_close_timer = lv.timer_create(
            self._auto_close_timer_cb, self.AUTO_CLOSE_MS, None
        )
        self.auto_close_timer.set_repeat_count(1)

    def _reset_auto_close_timer(self) -> None:
        if self._destroyed:
            return
        timer = self.auto_close_timer
        if timer is not None:
            timer.reset()
        else:
            self._start_auto_close_timer()

    def _stop_auto_close_timer(self) -> None:
        timer = self.auto_close_timer
        self.auto_close_timer = None
        if timer is None:
            return
        try:
            timer._del()
        except Exception as e:
            if __debug__:
                print(f"Error deleting charging auto-close timer: {e}")

    def _auto_close_timer_cb(self, timer) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        self._stop_auto_close_timer()

        if ChargingPromptScr._instance is self:
            ChargingPromptScr._instance = None

        self.clear_flag(lv.obj.FLAG.CLICKABLE)
        self._resume_camera_refresh()
        self.delete()

    def on_event(self, event_obj: lv.event_t):
        code = event_obj.code
        if code == lv.EVENT.CLICKED:
            lv.anim_del(self.anim_r.var, None)
            self.destroy()
        elif code == lv.EVENT.DELETE:
            self._resume_camera_refresh()
            ChargingPromptScr.reset()
            if get_elapsed() > 10000:
                ui.display.backlight(0)
            if __debug__:
                print("delete .......")

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        self._stop_auto_close_timer()

        if ChargingPromptScr._instance is self:
            ChargingPromptScr._instance = None

        self.clear_flag(lv.obj.FLAG.CLICKABLE)
        self._resume_camera_refresh()
        self.delete()
