import gc
from typing import TYPE_CHECKING

from storage import device
from trezor import loop, utils
from trezor.lvglui.scrs.components.anim import Anim

import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]

from . import lv_theme, theme_path_default, theme_path_png
from .components import slider
from .components.button import NormalButton
from .components.container import ContainerGrid
from .components.label import ScreenTitle, SubTitle, Title
from .components.navigation import Navigation
from .components.radio import Radio
from .widgets.style import StyleWrapper

if TYPE_CHECKING:
    from typing import Any

    pass

if __debug__:
    SETTINGS_MOVE_TIME = 120
    SETTINGS_MOVE_DELAY = 80

GO_PAGE_ANMI_TIME = 150
GO_PAGE_ANMI_DISTANCE = 60
BACK_PAGE_ANMI_TIME = 70
BACK_PAGE_ANMI_DISTANCE = 60


def apply_animations(targets, back=False, exclude_types=()):
    valid_targets = [t for t in targets if not isinstance(t, exclude_types)]

    def create_move_cb(targets_list):
        def cb(value):
            for target in targets_list:
                target.set_style_translate_x(value, 0)
                target.invalidate()

        return cb

    if valid_targets:
        move_anim = Anim(
            GO_PAGE_ANMI_DISTANCE if not back else (0 - BACK_PAGE_ANMI_DISTANCE),
            0,
            create_move_cb(valid_targets),
            time=GO_PAGE_ANMI_TIME if not back else BACK_PAGE_ANMI_TIME,
            delay=0,
            path_cb=lv.anim_t.path_ease_out,
        )
        move_anim.start()


class AnimScreen(lv.obj):
    """Singleton screen object."""

    def __init__(self, prev_scr=None, **kwargs):
        super().__init__()
        self.prev_scr = prev_scr or lv.scr_act()
        self.channel = loop.chan()
        self.add_style(StyleWrapper().bg_color(lv_theme.DT_BG).bg_opa(lv.OPA.COVER), 0)
        self.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        # panel to pin the screen size not scrolled
        self.content_area = lv.obj(self)
        self.content_area.set_size(lv.pct(100), 800)
        self.content_area.align(lv.ALIGN.TOP_MID, 0, 0)
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.ACTIVE)
        self.content_area.add_style(
            StyleWrapper()
            .bg_opa(lv.OPA.TRANSP)
            .pad_all(0)
            .border_width(0)
            .radius(0)
            .pad_bottom(15),
            0,
        )
        self.content_area.add_style(
            StyleWrapper().bg_color(lv_theme.DT_BG),
            lv.PART.SCROLLBAR | lv.STATE.DEFAULT,
        )
        self.content_area.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        if kwargs.get("nav_back", False):
            self.nav_back = Navigation(self.content_area)
            # self.nav_back.set_img(theme_path_png("nav-back"))
            self.nav_back.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
            # self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        if "title" in kwargs:
            self.title = ScreenTitle(self.content_area, None, (), kwargs["title"])
            self.title.set_width(lv.pct(78))
            self.title.set_long_mode(lv.label.LONG.DOT)
            self.title.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
            self.title.align(lv.ALIGN.TOP_MID, 0, 55)
        if "rti_btn_img" in kwargs:
            self.rti_btn = lv.imgbtn(self.content_area)
            self.rti_btn.set_size(48, 48)
            self.rti_btn.set_ext_click_area(100)
            self.rti_btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
            self.rti_btn.set_style_bg_img_src(kwargs["rti_btn_img"], 0)
            self.rti_btn.align(lv.ALIGN.TOP_RIGHT, -12, 55)
        if "icon_path" in kwargs:
            self.icon = lv.img(self.content_area)
            self.icon.set_src(kwargs["icon_path"])
            if hasattr(self, "nav_back"):
                self.icon.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 12, 8)
            else:
                self.icon.align(lv.ALIGN.TOP_LEFT, 12, 55)
            if "subtitle" in kwargs:
                self.subtitle = SubTitle(
                    self.content_area, None, (0, 16), kwargs["subtitle"]
                )
                self.subtitle.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 0)
        else:
            if "subtitle" in kwargs:
                self.subtitle = SubTitle(
                    self.content_area, self.title, (0, 16), kwargs["subtitle"]
                )
        if "btn_text" in kwargs:
            self.btn = NormalButton(self, kwargs["btn_text"])
            self.btn.enable(lv_theme.APP_CORRECT_BG)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        self.load_screen(self)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    # event callback
    def eventhandler(self, event_obj):
        event = event_obj.code
        target = event_obj.get_target()
        if event == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if isinstance(target, lv.imgbtn):
                if hasattr(self, "nav_back") and target in (
                    self.nav_back,
                    self.nav_back.nav_btn,
                ):  # .nav_btn:
                    if hasattr(self, "cb_nva_back_event"):
                        self.cb_nva_back_event()
                    elif self.prev_scr is not None:  #
                        self.load_screen(self.prev_scr, destroy_self=True)
                elif hasattr(self, "rti_btn") and target == self.rti_btn:
                    self.on_click_ext(target)
            else:
                if hasattr(self, "btn") and target == self.btn:
                    self.on_click(target)

    def on_click(self, target):
        pass

    def on_click_ext(self, target):
        pass

    async def request(self) -> Any:
        return await self.channel.take()

    def refresh(self):
        area = lv.area_t()
        area.x1 = 0
        area.y1 = 0
        area.x2 = 480
        area.y2 = 800
        self.invalidate_area(area)

    def collect_animation_targets(self) -> list:
        return []

    def _load_scr(self, scr: "Screen", back: bool = False) -> None:
        """Load a screen with container animation."""
        scr.invalidate()
        if device.is_animation_enabled() and isinstance(scr, AnimScreen):
            targets = []  # scr.collect_animation_targets()
            exclude_types = (
                Title,
                SubTitle,
                Navigation,
            )
            if targets:
                apply_animations(targets, back=back, exclude_types=exclude_types)
            lv.scr_load(scr)
        else:
            scr.set_pos(0, 0)
            lv.scr_load(scr)

    # NOTE:====================Functional Code Don't Edit========================

    def __new__(cls, pre_scr=None, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(lv.obj, cls).__new__(cls)
            utils.SCREENS.append(cls._instance)
        return cls._instance

    def load_screen(self, scr, destroy_self: bool = False):
        if destroy_self:
            self._load_scr(scr.__class__(), back=True)
            utils.try_remove_scr(self)
            self.del_delayed(1000)
            if hasattr(self.__class__, "_instance"):
                del self.__class__._instance
            del self
        else:
            self._load_scr(scr)

    def __del__(self):
        """Micropython doesn't support user defined __del__ now, so this not work at all."""
        try:
            self.delete()
        except BaseException:
            pass

    # NOTE:====================Functional Code Don't Edit========================


class Screen(lv.obj):
    """Singleton screen object."""

    def __init__(self, prev_scr=None, **kwargs):
        super().__init__()
        self.prev_scr = prev_scr or lv.scr_act()
        self.channel = loop.chan()
        self.add_style(StyleWrapper().bg_color(lv_theme.DT_BG).bg_opa(lv.OPA.COVER), 0)
        self.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        # panel to pin the screen size not scrolled
        self.content_area = lv.obj(self)
        self.content_area.set_size(lv.pct(100), 800)
        self.content_area.align(lv.ALIGN.TOP_MID, 0, 0)
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.ACTIVE)
        self.content_area.add_style(
            StyleWrapper()
            .bg_opa(lv.OPA.TRANSP)  # TRANSP
            .bg_color(lv_theme.DT_BG)
            .pad_all(0)
            .border_width(0)
            .radius(0)
            .pad_bottom(15),
            0,
        )
        self.content_area.add_style(
            StyleWrapper().bg_color(lv_theme.DT_BG),
            lv.PART.SCROLLBAR | lv.STATE.DEFAULT,
        )
        self.content_area.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        # nav_back
        if kwargs.get("nav_back", False):
            self.nav_back = Navigation(self.content_area)
            self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)
            self.nav_back.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        # icon
        if "icon_path" in kwargs:
            self.icon = lv.img(self.content_area)
            self.icon.set_src(kwargs["icon_path"])
            if hasattr(self, "nav_back"):
                self.icon.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 15, 14)
            else:
                self.icon.align(lv.ALIGN.TOP_MID, 0, 100)
        # rt_icon
        if "rti_path" in kwargs:
            self.rti_btn = lv.imgbtn(self.content_area)
            self.rti_btn.set_size(48, 48)
            self.rti_btn.set_ext_click_area(100)
            self.rti_btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
            self.rti_btn.set_style_bg_img_src(kwargs["rti_path"], 0)
            self.rti_btn.align(lv.ALIGN.TOP_RIGHT, -12, 56)
        # title
        if "title" in kwargs:
            self.title = Title(self.content_area, None, kwargs["title"])  # (),
            if hasattr(self, "icon"):
                self.title.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
            elif hasattr(self, "nav_back"):
                self.title.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 15, 14)
            else:
                self.title.align(lv.ALIGN.TOP_MID, 0, 100)
            self.title.text.align(lv.ALIGN.TOP_MID, 0, 0)
            self.title.text.add_style(StyleWrapper().text_align_center(), 0)
        # subtitle
        if "subtitle" in kwargs:
            self.subtitle = SubTitle(
                self.content_area, self.title, (0, 10), kwargs["subtitle"]
            )
            self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)
        # btn
        if "btn_text" in kwargs:
            self.btn = NormalButton(self, kwargs["btn_text"])
            self.btn.enable(lv_theme.APP_CORRECT_BG)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

        self.load_screen(self)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        # target = (
        #     event_obj.get_target()
        # )  # noqa: F841  # TODO: keep for future click-target handling
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)
        # elif code == lv.EVENT.CLICKED:
        #     if hasattr(self, "nav_back") and target == self.nav_back:# .nav_btn:
        #         if self.prev_scr is not None:  #
        #             self.load_screen(self.prev_scr, destroy_self=True)

    # event callback
    def eventhandler(self, event_obj):
        event = event_obj.code
        target = event_obj.get_target()
        if event == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if isinstance(target, lv.imgbtn):
                if hasattr(self, "nav_back") and target in (
                    self.nav_back,
                    self.nav_back.nav_btn,
                ):  # .nav_btn:
                    if self.prev_scr is not None:  #
                        self.load_screen(self.prev_scr, destroy_self=True)
                elif hasattr(self, "rti_btn") and target == self.rti_btn:
                    self.on_click_ext(target)
            else:
                if hasattr(self, "btn") and target == self.btn:
                    self.on_click(target)

    # click event callback
    def on_click(self, target):
        pass

    def on_click_ext(self, target):
        pass

    async def request(self) -> Any:
        return await self.channel.take()

    def refresh(self):
        area = lv.area_t()
        area.x1 = 0
        area.y1 = 0
        area.x2 = 480
        area.y2 = 800
        self.invalidate_area(area)

    def _load_scr(self, scr: "Screen", back: bool = False) -> None:
        # """Load a screen with animation."""
        scr.set_pos(0, 0)
        lv.scr_load(scr)

    # NOTE:====================Functional Code Don't Edit========================

    def __new__(cls, pre_scr=None, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(lv.obj, cls).__new__(cls)
            utils.SCREENS.append(cls._instance)
        return cls._instance

    def load_screen(self, scr, destroy_self: bool = False):
        if destroy_self:
            self._load_scr(scr.__class__(), back=True)
            utils.try_remove_scr(self)
            self.del_delayed(1000)
            if hasattr(self.__class__, "_instance"):
                del self.__class__._instance
            del self
            gc.collect()
            # pyright: off
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
            # pyright: on
        else:
            self._load_scr(scr)

    def __del__(self):
        """Micropython doesn't support user defined __del__ now, so this not work at all."""
        try:
            self.delete()
        except BaseException:
            pass

    # NOTE:====================Functional Code Don't Edit========================


class ANIM_DIRS:

    NONE = 0
    HOR = 1
    VER = 2


class FullSizeWindow(lv.obj):
    """Generic screen contains a title, a subtitle, and one or two button and a optional icon."""

    def __init__(
        self,
        title: str | None,
        subtitle: str | None,
        confirm_text: str = "",
        cancel_text: str = "",
        icon_path: str | None = None,
        icon_pad: int = 20,
        options: str | None = None,
        hold_confirm: bool = False,
        top_bg: bool = False,
        auto_close_ms: int = 0,
        anim_dir: int = ANIM_DIRS.HOR,
        primary_color=None,
        sub_icon_path: str | None = None,
        bg_color=None,
        button_layout: int = 1,
        title_icon_path: str | None = None,
        # subtitle_ver_off: int = 30,
        nav_back: bool = True,
        title_pos=None,
    ):
        super().__init__(lv.scr_act())
        self._pause_camera_refresh()
        if primary_color is None and not hold_confirm:
            primary_color = lv_theme.BTN_YES_BG
        if bg_color is None:
            bg_color = lv_theme.DT_BG
        if __debug__:
            self.layout_title = title
            self.layout_subtitle = subtitle

        self.channel = loop.chan()
        self.anim_dir = anim_dir
        try:
            self.set_size(lv.pct(100), lv.pct(100))
            pass
        except Exception as e:
            print("set size:", e)
        self.align(lv.ALIGN.TOP_MID, 0, 0)
        self.show_load_anim()
        self.add_style(
            StyleWrapper().bg_color(bg_color).pad_all(0).border_width(0).radius(0),
            0,
        )
        self.hold_confirm = hold_confirm
        if top_bg:
            self.top_background = lv.obj(self)
        self.content_area = lv.obj(self)
        self.content_area.set_size(lv.pct(100), lv.SIZE.CONTENT)
        self.content_area.align(lv.ALIGN.TOP_MID, 0, 0)
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.ACTIVE)
        self.content_area.add_style(
            StyleWrapper().pad_all(0).border_width(0).bg_opa(lv.OPA.TRANSP).radius(0),
            0,
        )
        self.content_area.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP).bg_color(lv_theme.DTL_BG),
            lv.PART.SCROLLBAR | lv.STATE.DEFAULT,
        )
        self.content_area.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        if nav_back:
            self.add_nav_back()
        else:
            self.content_area.align(lv.ALIGN.TOP_MID, 0, 40)

        self.icon_path = icon_path
        if icon_path:
            self.icon = lv.img(self.content_area)
            self.icon.remove_style_all()
            self.icon.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
            self.icon.set_src(icon_path)
            self.icon.align(lv.ALIGN.TOP_MID, 0, 16 if nav_back else 60)  # 12, 12)
            # for i in range(100000):
            # # while True
            #     w = self.icon.get_width()
            #     if w > 0:
            #         is_load_icon = False
            #         break
            if sub_icon_path:
                self.sub_icon = lv.img(self.content_area)
                self.sub_icon.remove_style_all()
                self.sub_icon.set_src(sub_icon_path)
                self.sub_icon.set_zoom(107)
                self.sub_icon.align_to(self.icon, lv.ALIGN.BOTTOM_RIGHT, 28, 28)

        if title:
            self.title = Title(
                self.content_area,
                self.icon if icon_path else None,
                title,
                icon_path=title_icon_path,
                relative_pos=title_pos
                if title_pos
                else (0, 28)
                if icon_path
                else (15, 14)
                if nav_back
                else (15, 60),
            )
            # self.title.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
            self.title.add_style(StyleWrapper().pad_all(0).max_width(450), 0)

            if subtitle is not None:
                if icon_path:
                    self.subtitle = SubTitle(
                        self.content_area, self.title, (0, 0), subtitle
                    )
                    self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 26)
                else:
                    self.subtitle = SubTitle(self.content_area, None, (0, 10), subtitle)
                    self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
                self.subtitle.add_style(StyleWrapper().max_width(450), 0)
        else:
            if hasattr(self, "icon") and self.icon:
                self.icon.align(lv.ALIGN.TOP_MID, 0, 0)
            if subtitle is not None:
                self.subtitle = SubTitle(
                    self.content_area, self.content_area, (15, 10), subtitle
                )
                if hasattr(self, "icon") and self.icon:
                    self.subtitle.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 60)
                else:
                    self.subtitle.align(lv.ALIGN.OUT_BOTTOM_MID, 15, 30)
        if options:
            self.content_area.set_height(600)
            self.selector = Radio(self.content_area, options, 400)
            self.selector.container.align_to(
                self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 15
            )
        else:
            # self.content_area.set_style_max_height(646, 0)
            self.content_area.set_style_min_height(440, 0)
            # self.content_area.set_style_max_width(480, 1)

        self.bnt_container = None
        if cancel_text and confirm_text:
            if button_layout == 1 and not hold_confirm:
                self.bnt_container = ContainerGrid(
                    self,  # .content_area,
                    row_dsc=[80, lv.GRID_TEMPLATE.LAST],
                    col_dsc=[217, 217, lv.GRID_TEMPLATE.LAST],
                    align_base=self.content_area,
                    pos=(0, 100),
                    pad_gap=15,
                )
                self.bnt_container.set_grid_align(
                    lv.GRID_ALIGN.SPACE_BETWEEN, lv.GRID_ALIGN.CENTER
                )
            else:
                self.bnt_container = ContainerGrid(
                    self,  # .content_area,
                    # self,
                    row_dsc=[80, 80, lv.GRID_TEMPLATE.LAST],
                    col_dsc=[450, lv.GRID_TEMPLATE.LAST],
                    align_base=self.content_area,
                    pos=(0, -76),  # pos=(0, 30)
                    pad_gap=15,
                )
                self.bnt_container.set_grid_align(
                    lv.GRID_ALIGN.CENTER, lv.GRID_ALIGN.SPACE_BETWEEN
                )

            # self.bnt_container.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
            self.btn_no = NormalButton(self.bnt_container, cancel_text)
            self.btn_no.add_style(
                StyleWrapper()
                .bg_color(lv_theme.BTN_CANCEL_BG)
                .text_color(lv_theme.BTN_CANCEL_FG)
                .bg_opa(),
                0,
            )
            if hold_confirm:
                self.slider = slider.Slider(
                    self.bnt_container,
                    confirm_text,
                    primary_color=primary_color,
                    relative_y=0,
                )
            else:
                self.btn_yes = NormalButton(self.bnt_container, confirm_text)
                self.btn_yes.enable(primary_color, text_color=lv_theme.BTN_YES_FG)
            if button_layout == 1 and not hold_confirm:
                self.btn_no.set_grid_cell(
                    lv.GRID_ALIGN.STRETCH, 0, 1, lv.GRID_ALIGN.STRETCH, 0, 1
                )
                self.btn_yes.set_grid_cell(
                    lv.GRID_ALIGN.STRETCH, 1, 1, lv.GRID_ALIGN.STRETCH, 0, 1
                )
            else:
                if hold_confirm:
                    self.slider.set_grid_cell(
                        lv.GRID_ALIGN.STRETCH, 0, 1, lv.GRID_ALIGN.STRETCH, 0, 1
                    )
                else:
                    self.btn_yes.set_grid_cell(
                        lv.GRID_ALIGN.STRETCH, 0, 1, lv.GRID_ALIGN.STRETCH, 0, 1
                    )
                self.btn_no.set_grid_cell(
                    lv.GRID_ALIGN.STRETCH, 0, 1, lv.GRID_ALIGN.STRETCH, 1, 1
                )
        # self.hold_confirm = hold_confirm
        # if self.hold_confirm and confirm_text:
        #     # self.content_area.set_style_max_height(520, 0)
        #     # self.content_area.add_style(
        #     #     StyleWrapper()
        #     #     .bg_opa(lv.OPA.COVER)
        #     #     .bg_color(lv_colors.UKEY_BLACK_3),
        #     #     0
        #     # )
        #     self.slider = slider.Slider(
        #                     self,
        #                     confirm_text,
        #                     primary_color=primary_color,
        #                     relative_y=-110
        #                 )
        #     if cancel_text:
        #         self.btn_no = NormalButton(self, cancel_text)
        #         self.btn_no.add_style(
        #             StyleWrapper()
        #             .bg_color(lv_theme.BTN_CANCEL_BG)
        #             .text_color(lv_theme.BTN_CANCEL_FG)
        #             .bg_opa()
        #             , 0,
        #         )
        if not self.bnt_container:
            print(f"not self.bnt_container - {cancel_text} - {confirm_text}")
            if cancel_text:
                self.btn_no = NormalButton(self, cancel_text)
                self.btn_no.add_style(
                    StyleWrapper()
                    .bg_color(lv_theme.BTN_CANCEL_BG)
                    .text_color(lv_theme.BTN_CANCEL_FG)
                    .bg_opa(),
                    0,
                )
                self.btn_no.align(lv.ALIGN.BOTTOM_MID, 0, -15)
            elif confirm_text:
                self.btn_yes = NormalButton(self, confirm_text)
                self.btn_yes.enable(primary_color, text_color=lv_theme.BTN_YES_FG)
                self.btn_yes.align(lv.ALIGN.BOTTOM_MID, 0, -15)

        if self.vibrate_necessary():
            self.vibrated = False
            self.add_event_cb(self.on_win_visible, lv.EVENT.DRAW_POST_END, None)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        self.clear_flag(lv.obj.FLAG.GESTURE_BUBBLE)
        if auto_close_ms:
            self.destroy(delay_ms=auto_close_ms)
        if __debug__:
            self.notify_change()
        if confirm_text:
            if hold_confirm:
                self.slider.add_event_cb(self.eventhandler, lv.EVENT.READY, None)
            else:
                self.btn_yes.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        if cancel_text:
            self.btn_no.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        self.add_event_cb(self._on_delete_resume_camera_refresh, lv.EVENT.DELETE, None)
        self.update_btn_layout(button_layout)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_MOMENTUM)
        self.clear_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.clear_flag(lv.obj.FLAG.SCROLL_MOMENTUM)

    def _pause_camera_refresh(self) -> None:
        self._camera_refresh_paused = False
        try:
            from trezor.qr import pause_camera_refresh

            pause_camera_refresh()
            self._camera_refresh_paused = True
        except Exception as e:
            if __debug__:
                print(f"Error pausing camera refresh: {e}")

    def _resume_camera_refresh(self) -> None:
        if not getattr(self, "_camera_refresh_paused", False):
            return
        self._camera_refresh_paused = False
        try:
            from trezor.qr import resume_camera_refresh

            resume_camera_refresh()
        except Exception as e:
            if __debug__:
                print(f"Error resuming camera refresh: {e}")

    def _on_delete_resume_camera_refresh(self, _event_obj) -> None:
        self._resume_camera_refresh()

    def update_btn_layout(self, button_layout=1):
        if hasattr(self, "bnt_container") and self.bnt_container:
            if button_layout == 0 or self.hold_confirm:
                # self.content_area.set_style_min_height(760, 0)
                self.content_area.set_style_max_height(480, 0)
                self.bnt_container.align_to(self, lv.ALIGN.OUT_BOTTOM_MID, 0, -190)
                # self.bnt_container.align_to(self, lv.ALIGN.BOTTOM_MID, 0, -190)
            elif button_layout == 1:
                # self.content_area.add_style(
                #     StyleWrapper()
                #     .bg_opa(lv.OPA.COVER)
                #     .bg_color(lv_colors.UKEY_RED_2),
                #     0
                # )
                self.content_area.set_style_max_height(575, 0)  #
                self.bnt_container.align_to(self, lv.ALIGN.BOTTOM_MID, 0, -15)
        else:
            if hasattr(self, "btn_yes"):
                self.content_area.set_style_max_height(575, 0)
                self.btn_yes.align_to(self, lv.ALIGN.BOTTOM_MID, 0, -15)
            elif hasattr(self, "btn_no"):
                self.content_area.set_style_max_height(575, 0)
                self.btn_no.align_to(self, lv.ALIGN.BOTTOM_MID, 0, -15)
        # self.content_area.set_style_max_height(760, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_win_visible(self, _event_obj):
        from trezor import motor

        if __debug__:
            print("on_draw_post_end called.")
        if self.vibrated:
            self.remove_event_cb(None)
            return
        self.vibrated = True
        self.remove_event_cb(None)
        if __debug__:
            print("vibrate start...")
        if self.icon_path == theme_path_png("success"):
            motor.vibrate(motor.SUCCESS)
        elif self.icon_path == theme_path_png(
            "tools/triangle-warning"
        ) or self.icon_path == theme_path_png("triangle-error"):
            motor.vibrate(motor.WARNING)
        elif self.icon_path == theme_path_png("danger"):
            motor.vibrate(motor.ERROR)

    def vibrate_necessary(self) -> bool:
        if not hasattr(self, "icon"):
            return False
        if __debug__:
            print(f"vibrate necessary ? {self.icon_path}")
        if self.icon_path in [
            theme_path_default("success.png"),
            theme_path_png("triangle-warning"),
            theme_path_default("danger.png"),
            theme_path_png("success"),
            theme_path_png("triangle-warning"),
            theme_path_png("triangle-error"),
            theme_path_png("danger"),
        ]:
            if __debug__:
                print("vibrate necessary: true")
            return True
        return False

    def btn_layout_ver(self):
        if not all([hasattr(self, "btn_no"), hasattr(self, "btn_yes")]):
            return
        self.content_area.set_style_max_height(520, 0)
        self.btn_no.set_size(450, 80)
        self.btn_no.align(lv.ALIGN.BOTTOM_MID, 0, -8)
        self.btn_yes.set_size(450, 80)
        self.btn_yes.align_to(self.btn_no, lv.ALIGN.OUT_TOP_MID, 0, -8)

    def add_nav_back(self):
        """
        Add a navigation back button to the screen. The nav_back button is aligned to the left of the screen.
        If added, add a event handler called <on_nav_back> or override the method <eventhandler>
        when you need to handle the back event specifically.
        """
        self.nav_back = Navigation(self)
        if any([hasattr(self, "btn_no"), hasattr(self, "btn_yes")]):
            self.content_area.set_style_max_height(574, 0)
        self.content_area.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 14)
        self.content_area.set_style_min_height(440, 0)
        # self.content_area.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 0)
        if hasattr(self, "icon"):
            self.icon.align(lv.ALIGN.TOP_MID, 0, 14)
        self.nav_back.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        # self.nav_back.nav_btn.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

    def add_nav_back_right(self, icon="cancel"):
        """
        Add a navigation back button to the screen. The nav_back button is aligned to the right of the screen.
        If added, add a event handler called <on_nav_back> or override the method <eventhandler>
        when you need to handle the back event specifically.
        """
        self.nav_back_right = Navigation(
            self,
            btn_bg_img=theme_path_default(f"{icon}.png"),
            nav_btn_align=lv.ALIGN.RIGHT_MID,
            align=lv.ALIGN.TOP_RIGHT,
            pos=(-20, 40),
        )
        # if any([hasattr(self, "btn_no"), hasattr(self, "btn_yes")]):
        #     self.content_area.set_style_max_height(574, 0)
        # self.content_area.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_RIGHT, 0, 0)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if hasattr(self, "btn_no") and target == self.btn_no:
                self.show_dismiss_anim()
                self.channel.publish(0)
            elif hasattr(self, "btn_yes") and target == self.btn_yes:
                self.show_unload_anim()
                if hasattr(self, "selector"):
                    self.channel.publish(self.selector.get_selected_str())
                else:
                    if not self.hold_confirm:
                        self.channel.publish(1)
            elif hasattr(self, "nav_back") and target in (
                self.nav_back,
                self.nav_back.nav_btn,
            ):  # .nav_btn:
                if not hasattr(self, "on_nav_back"):
                    self.show_dismiss_anim()
                    self.channel.publish(0)
                else:
                    self.on_nav_back(event_obj)
        elif code == lv.EVENT.READY and self.hold_confirm:
            if target == self.slider:
                self.show_dismiss_anim()
                self.channel.publish(1)

    async def request(self) -> Any:
        if __debug__:
            from apps.debug import confirm_signal, input_signal
            from trezor.ui import Result

            value = None
            # return await loop.race(confirm_signal(),self.channel.take())
            try:
                value = await loop.race(
                    confirm_signal(), input_signal(), self.channel.take()
                )
            except Result as result:
                # Result exception was raised, this means this layout is complete.

                value = result.value
            return value

        else:
            return await self.channel.take()

    if __debug__:

        def notify_change(self):
            from apps.debug import notify_layout_change

            notify_layout_change(self)

        def read_content(self) -> list[str]:
            return [self.layout_title or ""] + [self.layout_subtitle or ""]

    def destroy(self, delay_ms=400):
        try:
            self.del_delayed(delay_ms)
        except Exception:
            pass

    def _delete_cb(self, _anim):
        try:
            self.del_delayed(100)
        except Exception:
            pass

    def _load_anim_hor(self):
        Anim(
            480,
            0,
            self._set_x,
            time=120 if not __debug__ else SETTINGS_MOVE_TIME,
            delay=80 if not __debug__ else SETTINGS_MOVE_DELAY,
        ).start_anim()

    def _load_anim_ver(self):
        self.set_y(800)
        Anim(
            800,
            0,
            self._set_y,
            time=120 if not __debug__ else SETTINGS_MOVE_TIME,
            delay=80 if not __debug__ else SETTINGS_MOVE_DELAY,
        ).start_anim()

    def _set_y(self, y):
        try:
            self.set_y(y)
        except Exception:
            pass

    def _set_x(self, x):
        try:
            self.set_x(x)
        except Exception:
            pass

    def _dismiss_anim_hor(self):
        Anim(
            0,
            480,
            self._set_x,
            time=120 if not __debug__ else SETTINGS_MOVE_TIME,
            delay=80 if not __debug__ else SETTINGS_MOVE_DELAY,
            del_cb=self._delete_cb,
        ).start_anim()

    def _dismiss_anim_ver(self):
        Anim(
            0,
            800,
            self._set_y,
            time=120 if not __debug__ else SETTINGS_MOVE_TIME,
            delay=80 if not __debug__ else SETTINGS_MOVE_DELAY,
            del_cb=self._delete_cb,
        ).start_anim()

    def show_load_anim(self):
        self.set_pos(0, 0)
        return

    def show_dismiss_anim(self):
        self.destroy()
        return

    def show_unload_anim(self):
        # if self.anim_dir == ANIM_DIRS.HOR:
        #     Anim(0, -480, self.set_pos, time=200, y_axis=False, delay=200, del_cb=self._delete).start()
        # else:
        #     self.show_dismiss_anim()
        self.destroy(1100)

    def refresh(self):
        area = lv.area_t()
        area.x1 = 0
        area.y1 = 0
        area.x2 = 480
        area.y2 = 800
        self.invalidate_area(area)
