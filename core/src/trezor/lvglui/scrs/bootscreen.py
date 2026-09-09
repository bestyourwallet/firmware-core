from . import lv_theme, theme_path_default
from .common import Screen, lv  # noqa: F401,F403, F405
from .widgets.style import StyleWrapper


class BootScreen(Screen):
    def __init__(self):
        super().__init__()
        self.add_style(
            StyleWrapper().bg_color(lv_theme.APP_BLACK_FG),
            lv.STATE.DEFAULT,
        )
        self.img = lv.img(self)
        self.img.set_src(theme_path_default("tools_logo-black.png"))
        self.img.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)  # 72
        self.img.align(lv.ALIGN.TOP_MID, 0, 137)
        self.label = lv.img(self)
        self.label.set_src(theme_path_default("tools_logo-label.png"))
        self.label.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
        # self.label.align(lv.ALIGN.BOTTOM_MID, 0, -86)
        self.label.align_to(self.img, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)

        self.bar = lv.bar(self)
        self.bar.set_size(226, 6)
        self.bar.align_to(self.label, lv.ALIGN.OUT_BOTTOM_MID, 0, 330)

        self.bar.add_style(
            StyleWrapper()
            .bg_color(lv_theme.BOOT_BAR_BG)
            .bg_opa(255)
            .border_color(lv_theme.BOOT_BAR_FG)
            .border_opa(255)
            .border_width(0),
            lv.PART.MAIN | lv.STATE.DEFAULT,
        )
        self.bar.add_style(
            StyleWrapper().bg_color(lv_theme.BOOT_BAR_FG),
            lv.PART.INDICATOR | lv.STATE.DEFAULT,
        )
        self.bar.set_style_bg_opa(255, lv.PART.INDICATOR | lv.STATE.DEFAULT)
        self.bar.set_style_anim_time(200, lv.PART.MAIN)
        self.bar.set_value(100, lv.ANIM.ON)

    def set_resource_progress(
        self, current: int, total: int, _status: str, _name: str | None
    ) -> None:
        progress = current * 100 // total if total else 0
        self.bar.set_value(progress, lv.ANIM.OFF)
        lv.timer_handler()

    def load_screen(self, scr, _destroy_self: bool = False):
        import lvgl as lv  # type: ignore [Import "lvgl" could not be resolved]

        return lv.scr_load(scr)

    # def eventhandler(self, event_obj):
    #     code = event_obj.code
    #     if code == lv.EVENT.SCREEN_LOADED:
    #         print(f'draw end')
    #         self.channel.publish("boot_screen_done")
    #     else:
    #         print(f'clicked boot')
