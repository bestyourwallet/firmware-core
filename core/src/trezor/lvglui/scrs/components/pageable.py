from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import font_GeistRegular30, lv, lv_theme, theme_path_png
from ..common import AnimScreen, FullSizeWindow
from ..widgets.style import StyleWrapper
from .anim import Anim
from .button import NormalButton
from .container import ContainerFlexRow


class PageAbleMessage(FullSizeWindow):
    def __init__(
        self,
        title: str,
        content: str,
        channel,
        primary_color=lv_theme.APP_CORRECT_BG,
        confirm_text=_(i18n_keys.BUTTON__CONTINUE),
        cancel_text=_(i18n_keys.BUTTON__REJECT),
        page_size: int = 240,
        font=font_GeistRegular30,
    ):
        super().__init__(
            title,
            None,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            primary_color=primary_color,
            anim_dir=0,
        )

        self.content = content
        self.page_size = page_size
        if channel:
            self.channel = channel
        else:
            self.add_nav_back()
            self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.panel = lv.obj(self.content_area)
        self.panel.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.panel.add_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)
        self.panel.add_style(
            StyleWrapper()
            .width(456)
            .height(lv.SIZE.CONTENT)
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa()
            .border_width(0)
            .pad_ver(16)
            .pad_hor(24)
            .radius(40)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_font(font)
            .text_align_left()
            .text_letter_space(-1),
            0,
        )
        self.panel.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        # content
        self.message = lv.label(self.panel)
        self.message.set_long_mode(lv.label.LONG.WRAP)
        self.message.set_size(lv.pct(100), lv.SIZE.CONTENT)
        self.message.add_style(StyleWrapper().text_letter_space(-2), 0)
        self.message.set_text(content[: self.page_size])
        # # close button
        # self.close = NormalButton(self, cancel_text)
        self.container = ContainerFlexRow(self, None, padding_col=5)
        self.container.set_size(lv.SIZE.CONTENT, 30)
        self.container.add_style(
            StyleWrapper().pad_all(5)
            # .bg_color(lv_colors.UKEY_O_RED_3)
            # .bg_opa(lv.OPA.COVER)
            ,
            0,
        )
        # self.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_colors.UKEY_O_RED_3)
        #     .bg_opa(lv.OPA.COVER)
        #     , 0
        # )
        self.pages_size = len(content) // self.page_size + 1
        if self.pages_size > 1:
            # indicator dots
            self.select_index = 0
            self.indicators = []
            for i in range(self.pages_size):
                self.indicators.append(Indicator(self.container, self, i))
            self.clear_flag(lv.obj.FLAG.GESTURE_BUBBLE)
            self.add_event_cb(self.on_gesture, lv.EVENT.GESTURE, None)
        self.container.align_to(self.message, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)

    def on_gesture(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            indev = lv.indev_get_act()
            _dir = indev.get_gesture_dir()
            if _dir not in [lv.DIR.RIGHT, lv.DIR.LEFT]:
                return
            self.indicators[self.select_index].set_active(False)
            if _dir == lv.DIR.LEFT:
                self.select_index = (self.select_index + 1) % self.pages_size

            elif _dir == lv.DIR.RIGHT:
                self.select_index = (
                    self.select_index - 1 + self.pages_size
                ) % self.pages_size
            else:
                return
            self.indicators[self.select_index].set_active(True)
            self.message.set_text(
                self.content[
                    self.page_size
                    * self.select_index : self.page_size
                    * (self.select_index + 1)
                ]
            )

    def show_page(self, page_index: int):
        self.indicators[self.select_index].set_active(False)
        self.select_index = page_index
        self.message.set_text(
            self.content[
                self.page_size
                * self.select_index : self.page_size
                * (self.select_index + 1)
            ]
        )
        self.indicators[self.select_index].set_active(True)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED and target == self.nav_back.nav_btn:
            self.destroy(50)


class PageByButtonAnimScreen(AnimScreen):
    def __init__(
        self,
        prev_scr,
        title: str,
        nav_back,
        boundary=True,
        rti_btn=None,
    ):
        kwargs = {
            "prev_scr": prev_scr,
            "title": title,
            "nav_back": nav_back,
            "rti_btn_img": rti_btn,
        }
        super().__init__(**kwargs)
        self.animations_next = []
        self.animations_prev = []
        self.boundary = boundary

    def init_buttons(self, max_pages: int = 0, current_page: int = 0):
        self.max_pages = max_pages
        self.current_page = current_page

        if self.max_pages > 0:
            self.enable_style = (
                StyleWrapper()
                .bg_color(lv_theme.BTN_CANCEL_BG)
                .bg_opa(lv.OPA.COVER)
                .radius(80)
            )

            self.next_btn = NormalButton(self, "")
            self.next_btn.set_size(217, 80)
            self.next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -15, -15)
            self.next_btn.set_style_bg_img_src(theme_path_png("arrow-right-2"), 0)
            self.next_btn.add_style(self.enable_style, 0)

            self.back_btn = NormalButton(self, "")
            self.back_btn.set_size(217, 80)
            self.back_btn.align(lv.ALIGN.BOTTOM_LEFT, 15, -15)
            self.back_btn.add_style(
                StyleWrapper()
                .bg_img_src(theme_path_png("arrow-left-gray"))
                .bg_color(lv_theme.CONT_ITEM_DBG),
                0,
            )
            if not self.boundary or current_page > 0:
                self.back_btn.set_style_bg_img_src(theme_path_png("arrow-left-2"), 0)
            else:
                self.back_btn.clear_flag(lv.btn.FLAG.CLICKABLE)
            # self.back_btn.add_style(self.enable_style, 0)

    def animate_list_items(self):
        def create_move_cb_container(obj, item_index):
            def cb(value):
                obj.set_style_translate_x(value, 0)
                obj.invalidate()

            return cb

        container_move_anim = Anim(
            50,
            0,
            create_move_cb_container(self.container, 0),
            time=150,
            delay=0,
            path_cb=lv.anim_t.path_ease_out,
        )

        container_move_back_anim = Anim(
            -50,
            0,
            create_move_cb_container(self.container, 0),
            time=150,
            delay=0,
            path_cb=lv.anim_t.path_ease_out,
        )

        self.animations_next.append(container_move_anim)
        container_move_anim.start()

        self.animations_prev.append(container_move_back_anim)

    def enable_page_buttons(self, btn):
        btn.add_flag(lv.btn.FLAG.CLICKABLE)
        btn.set_style_bg_img_src(
            theme_path_png("arrow-right-2")
            if btn == self.next_btn
            else theme_path_png("arrow-left-2"),
            0,
        )

    def disable_page_buttons(self, btn):
        btn.clear_flag(lv.btn.FLAG.CLICKABLE)
        btn.set_style_bg_img_src(
            theme_path_png("arrow-right-gray")
            if btn == self.next_btn
            else theme_path_png("arrow-left-gray"),
            0,
        )

    def update_page_buttons(self):
        if (self.current_page == 0 and self.boundary) or self.max_pages == 0:
            self.disable_page_buttons(self.back_btn)
        elif not self.back_btn.has_flag(lv.btn.FLAG.CLICKABLE):
            self.enable_page_buttons(self.back_btn)

        if (
            self.current_page == self.max_pages and self.boundary
        ) or self.max_pages == 0:
            self.disable_page_buttons(self.next_btn)
        elif not self.next_btn.has_flag(lv.btn.FLAG.CLICKABLE):
            self.enable_page_buttons(self.next_btn)

    def next_page(self):
        if self.current_page < self.max_pages:
            self.current_page += 1
            # self._create_visible_chain_buttons()
            for anim in self.animations_next:
                anim.start()
            self.update_page_buttons()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            # self._create_visible_chain_buttons()
            for anim in self.animations_prev:
                anim.start()
            self.update_page_buttons()

    def eventhandler_(self, event_obj):
        event = event_obj.code
        target = event_obj.get_target()
        if event == lv.EVENT.CLICKED:
            if hasattr(self, "back_btn") and target == self.back_btn:
                self.prev_page()
            elif hasattr(self, "next_btn") and target == self.next_btn:
                self.next_page()


class Indicator(lv.btn):
    def __init__(self, parent, target, index):
        super().__init__(parent)
        self.index = index
        self.set_size(15, 15)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa(lv.OPA.COVER)
            .border_width(0)
            .radius(8)
            .pad_all(2),
            0,
        )
        self.add_style(
            StyleWrapper().outline_width(0).outline_opa(lv.OPA.TRANSP),
            lv.PART.MAIN | lv.STATE.FOCUS_KEY,
        )
        self.active = False
        if index == 0:
            self.set_active(True)
        self.target = target

        self.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

    def set_active(self, active):
        if active:
            self.active = True
            self.set_style_bg_color(lv_theme.CONT_ITEM_PFG, 0)
        else:
            self.active = False
            self.set_style_bg_color(lv_theme.CONT_ITEM_BG, 0)

    def on_click(self, event):
        code = event.code
        if code == lv.EVENT.CLICKED:
            if self.target and hasattr(self.target, "show_page"):
                self.target.show_page(self.index)
