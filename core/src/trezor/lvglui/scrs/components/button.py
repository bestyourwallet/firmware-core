from trezor import motor
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import (
    font_GeistRegular20,
    font_GeistRegular26,
    font_GeistSemiBold26,
    font_GeistSemiBold30,
    lv,
    lv_theme,
    theme_path_png,
)
from ..widgets.style import StyleWrapper
from .line import Line
from .transition import BtnClickTransition, DefaultTransition


class NormalButton(lv.btn):
    def __init__(
        self,
        parent,
        text=None,
        enable=True,
        pressed_style=None,
        label_align=lv.ALIGN.CENTER,
    ) -> None:
        super().__init__(parent)
        if text is None:
            text = _(i18n_keys.BUTTON__NEXT)
        self.remove_style_all()
        self.set_size(450, 80)
        self.align_to(parent, lv.ALIGN.BOTTOM_MID, 0, -15)
        self.add_style(
            StyleWrapper()
            .radius(98)
            .bg_opa(lv.OPA.COVER)
            .text_opa(lv.OPA.COVER)
            .text_letter_space(-1)
            .pad_hor(24)
            .pad_ver(30)
            .text_font(font_GeistSemiBold30),
            0,
        )
        if enable:
            self.enable()
        else:
            self.disable()
        self.add_style(
            pressed_style
            or StyleWrapper()
            .bg_opa(lv.OPA._60)
            .transform_height(-2)
            .transform_width(-2)
            .transition(BtnClickTransition()),
            lv.PART.MAIN | lv.STATE.PRESSED,
        )
        # the next btn label
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.label = lv.label(self)
        self.label.set_size(360, lv.SIZE.CONTENT)
        self.label.set_long_mode(lv.label.LONG.WRAP)
        self.label.add_style(
            StyleWrapper().max_width(360).max_height(80).text_align_center(),
            0,
        )
        self.label.add_flag(lv.obj.FLAG.SCROLLABLE)
        self.label.set_scroll_dir(lv.DIR.VER)
        self.label.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.label.set_text(text)
        self.label.set_align(label_align)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        self.click_mask = lv.obj(self)
        self.click_mask.add_style(
            StyleWrapper()
            .height(50)
            .width(140)
            .align(lv.ALIGN.CENTER)
            .bg_opa(lv.OPA.TRANSP)
            .border_width(0),
            0,
        )
        self.click_mask.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.click_mask.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

    def disable(self, bg_color=None, text_color=None) -> None:
        if bg_color is None:
            bg_color = lv_theme.BTN_YES_DBG
        if text_color is None:
            text_color = lv_theme.BTN_YES_DFG
        self.add_style(StyleWrapper().bg_color(bg_color).text_color(text_color), 0)
        self.clear_flag(lv.btn.FLAG.CLICKABLE)

    def enable(self, bg_color=None, text_color=None) -> None:
        if bg_color is None:
            bg_color = lv_theme.BTN_YES_BG
        if text_color is None:
            text_color = lv_theme.BTN_YES_FG
        self.add_style(StyleWrapper().bg_color(bg_color).text_color(text_color), 0)
        self.add_flag(lv.btn.FLAG.CLICKABLE)

    def enable_no_bg_mode(self, skip_pressed_style=False):
        self.add_style(StyleWrapper().bg_color(lv_theme.BTN_YES_DBG), 0)
        if not skip_pressed_style:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.BTN_YES_DBG).bg_opa(),
                lv.PART.MAIN | lv.STATE.PRESSED,
            )
        self.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.click_mask.add_flag(lv.obj.FLAG.CLICKABLE)


class ListItemBtn(lv.btn):
    def __init__(
        self,
        parent,
        text: str,
        right_text="",
        left_img_src: str = "",
        has_next: bool = False,
        has_bgcolor=True,
        use_transition=True,
        min_height=100,
        pad_ver=0,
        bot_line=False,
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.unique_bg = has_bgcolor
        self.set_size(450, lv.SIZE.CONTENT)
        self.min_height = min_height
        self.add_style(
            StyleWrapper()
            # .bg_color(lv_colors.UKEY_WHITE_1 if has_bgcolor else lv_colors.UKEY_WHITE_1)
            .bg_opa(lv.OPA.TRANSP)
            .min_height(min_height)
            .text_font(font_GeistSemiBold26)
            .bg_color(lv_theme.CONT_ITEM_BG)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_letter_space(-1)
            .pad_hor(15)
            .pad_ver(pad_ver)
            .pad_top(0),
            0,
        )
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.use_transition = use_transition
        if use_transition:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.CONT_ITEM_PBG).bg_opa(lv.OPA.COVER)
                # .transform_height(-2)
                # .transform_width(-4)
                # .transition(DefaultTransition())
                ,
                lv.PART.MAIN | lv.STATE.PRESSED,
            )
        # if left_img_src:
        #     self.img_left = lv.img(self)
        #     self.img_left.align(lv.ALIGN.LEFT_MID, -2, 0)
        #     self.img_left.add_flag(lv.obj.FLAG.CLICKABLE)
        self.update_left_img(left_img_src)
        if has_next:
            self.img_right = lv.img(self)
            self.img_right.set_src(theme_path_png("arrow-right"))
            self.img_right.set_align(lv.ALIGN.RIGHT_MID)
        self.label_left = lv.label(self)
        self.label_left.set_width(360)
        self.label_left.set_long_mode(lv.label.LONG.WRAP)
        self.label_left.set_text(text)
        self.label_left.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold26)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_letter_space(-1)
            .text_align_left(),
            0,
        )

        if left_img_src:
            self.label_left.align_to(self.img_left, lv.ALIGN.OUT_RIGHT_MID, 16, 0)  # 16
        else:
            self.label_left.set_align(lv.ALIGN.LEFT_MID)
        if right_text:
            self.label_right = lv.label(self)
            self.label_right.set_long_mode(lv.label.LONG.WRAP)
            self.label_right.set_width(225)
            self.label_right.set_text(right_text)
            self.label_right.add_style(
                StyleWrapper()
                .text_font(font_GeistRegular26)
                .text_color(lv_theme.CONT_ITEM_SUB_FG)
                .text_letter_space(-1)
                .text_align_right(),
                0,
            )
            if has_next:
                self.label_right.align_to(self.img_right, lv.ALIGN.OUT_LEFT_MID, -10, 0)
            else:
                self.label_right.align(lv.ALIGN.RIGHT_MID, 0, 0)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        if bot_line:
            self.bot_line = Line(self, 420)
            self.bot_line.align_to(self, lv.ALIGN.BOTTOM_MID, 0, 0)
            # line_points = [{"x": 0, "y": 0}, {"x": 420, "y": 0}]
            # style_line = lv.style_t()
            # style_line.init()
            # style_line.set_line_color(lv_theme.CONT_ITEM_BLINE)
            # style_line.set_line_width(1)
            # self.bot_line = lv.line(self)
            # self.bot_line.remove_style_all()
            # self.bot_line.set_points(line_points, 2)
            # self.bot_line.add_style(style_line, 0)

    def refresh_theme(self, left_img_src=None):
        self.set_style_bg_color(lv_theme.CONT_ITEM_BG, 0)
        if self.use_transition:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.CONT_ITEM_PBG).bg_opa(lv.OPA.COVER),
                lv.PART.MAIN | lv.STATE.PRESSED,
            )

        self.label_left.set_style_text_color(lv_theme.CONT_ITEM_FG, 0)
        if hasattr(self, "label_right") and self.label_right is not None:
            self.label_right.set_style_text_color(lv_theme.CONT_ITEM_SUB_FG, 0)
        if hasattr(self, "bot_line") and self.bot_line is not None:
            self.bot_line.set_style_line_color(lv_theme.CONT_ITEM_BLINE, 0)
        if left_img_src is not None and hasattr(self, "icon") and self.icon is not None:
            self.icon.set_src(left_img_src)

    def hide_bot_line(self):
        if hasattr(self, "bot_line") and not self.bot_line.has_flag(lv.obj.FLAG.HIDDEN):
            self.bot_line.add_flag(lv.obj.FLAG.HIDDEN)

    def show_bot_line(self):
        if hasattr(self, "bot_line") and self.bot_line.has_flag(lv.obj.FLAG.HIDDEN):
            self.bot_line.clear_flag(lv.obj.FLAG.HIDDEN)
        elif not hasattr(self, "bot_line"):
            self.bot_line = Line(self, 420)
            self.bot_line.align_to(self, lv.ALIGN.BOTTOM_MID, 0, 0)

    def add_check_img(self) -> None:
        self.img_right = lv.img(self)
        self.img_right.set_src(theme_path_png("checked-solid"))
        self.img_right.align(lv.ALIGN.RIGHT_MID, -15, 0)
        self.img_right.add_flag(lv.obj.FLAG.HIDDEN)

    def set_checked(self) -> None:
        if self.img_right.has_flag(lv.obj.FLAG.HIDDEN):
            self.img_right.clear_flag(lv.obj.FLAG.HIDDEN)
            # self.label_left.set_style_text_color(lv_colors.WHITE, 0)
            if not self.unique_bg:
                self.add_style(StyleWrapper().bg_color(lv_theme.CONT_ITEM_PBG), 0)

    def set_uncheck(self) -> None:
        if not self.img_right.has_flag(lv.obj.FLAG.HIDDEN):
            self.img_right.add_flag(lv.obj.FLAG.HIDDEN)
            # self.label_left.set_style_text_color(lv_colors.WHITE_2, 0)
            if not self.unique_bg:
                self.add_style(StyleWrapper().bg_color(lv_theme.CONT_ITEM_BG), 0)

    def is_unchecked(self) -> bool:
        return self.img_right.has_flag(lv.obj.FLAG.HIDDEN)

    def text_layout_vertical(self, pad_top: int = 23, pad_ver: int = 23) -> None:
        assert hasattr(self, "img_left"), "No left image"
        self.add_style(
            StyleWrapper()
            .pad_ver(pad_ver)
            .pad_top(pad_top)
            .min_height(self.min_height),
            0,
        )
        self.label_left.align_to(self.img_left, lv.ALIGN.OUT_RIGHT_TOP, 16, 0)
        self.label_right.set_width(344)
        self.label_left.add_style(StyleWrapper().pad_all(0), 0)
        self.label_right.add_style(
            StyleWrapper().text_font(font_GeistRegular20).text_align_left().pad_all(0),
            0,
        )
        self.label_right.align_to(self.label_left, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 4)

    def update_left_img(self, left_img_src: str) -> None:
        if not hasattr(self, "img_left"):
            self.img_left = lv.img(self)
            # if left_img_src != 'null':
            #     self.img_left.set_src(left_img_src)
            self.img_left.align(lv.ALIGN.LEFT_MID, -2, 0)
            self.img_left.add_flag(lv.obj.FLAG.CLICKABLE)
        if left_img_src:
            self.img_left.set_src(left_img_src)
            if hasattr(self, "label_left"):
                self.label_left.align_to(self.img_left, lv.ALIGN.OUT_RIGHT_MID, 16, 0)

    def disable(self) -> None:
        self.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_ITEM_DBG),  # UKEY_GRAY_1
            0,
        )
        self.label_left.set_style_text_color(lv_theme.CONT_ITEM_DFG, 0)  # WHITE_2
        if hasattr(self, "label_right"):
            self.label_right.set_style_text_color(lv_theme.CONT_ITEM_RIGHT_DFG, 0)
        self.clear_flag(lv.obj.FLAG.CLICKABLE)


class ListItemBtnWithSwitch(lv.btn):
    def __init__(
        self, parent, text: str, is_haptic_feedback: bool = False, bot_line=False
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.is_haptic_feedback = is_haptic_feedback
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_BG)
            .min_height(100)
            .bg_opa(lv.OPA.COVER)
            .radius(0)
            .pad_hor(15)
            .text_font(font_GeistSemiBold26)
            .text_letter_space(-1)
            .text_color(lv_theme.CONT_ITEM_FG),
            0,
        )
        self.add_style(
            StyleWrapper()
            # .bg_color(lv_colors.UKEY_O_BLACK_2)
            .transition(DefaultTransition()),
            lv.PART.MAIN | lv.STATE.PRESSED,
        )

        self.label_left = lv.label(self)
        self.label_left.set_size(350, lv.SIZE.CONTENT)
        self.label_left.set_text(text)
        self.label_left.set_long_mode(lv.label.LONG.WRAP)
        self.label_left.set_align(lv.ALIGN.LEFT_MID)
        self.switch = lv.switch(self)
        self.switch.set_size(70, 38)
        self.switch.set_align(lv.ALIGN.RIGHT_MID)
        self.switch.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

        self.switch.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_ITEM_SW_BG).radius(19), 0
        )
        self.switch.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_ITEM_SW_PBG).radius(19),
            lv.PART.INDICATOR | lv.STATE.CHECKED,
        )
        self.switch.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_ITEM_SW_FG).pad_all(-2),  # WHITE
            lv.PART.KNOB | lv.STATE.DEFAULT,
        )
        self.switch.add_state(lv.STATE.CHECKED)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        if bot_line:
            self.bot_line = Line(self, 420)
            self.bot_line.align_to(self, lv.ALIGN.BOTTOM_MID, 0, 0)

    def eventhandler(self, event) -> None:
        code = event.code
        target = event.get_target()
        if code == lv.EVENT.CLICKED and target != self.switch:
            # self.set_state(self.get_state())
            if self.switch.get_state() == lv.STATE.CHECKED:
                self.clear_state()
            else:
                self.add_state()
            lv.event_send(self.switch, lv.EVENT.VALUE_CHANGED, None)
        elif code == lv.EVENT.PRESSED:
            if not self.is_haptic_feedback:
                motor.vibrate(motor.WHISPER)
            else:
                # if self.switch.get_state() != lv.STATE.CHECKED:
                #     motor.vibrate(motor.WHISPER, force=True)
                motor.vibrate(motor.WHISPER, force=True)

    def clear_state(self) -> None:
        self.switch.clear_state(lv.STATE.CHECKED)

    def add_state(self) -> None:
        self.switch.add_state(lv.STATE.CHECKED)

    def set_state(self, stat) -> None:
        if stat:
            self.switch.add_state(lv.STATE.CHECKED)
        else:
            self.switch.clear_state(lv.STATE.CHECKED)

    def get_state(self) -> bool:
        return self.switch.has_state(lv.STATE.CHECKED)

    def refresh_theme(self, left_img_src=None):
        self.set_style_bg_color(lv_theme.CONT_ITEM_BG, 0)
        self.label_left.set_style_text_color(lv_theme.CONT_ITEM_FG, 0)
        if hasattr(self, "label_right") and self.label_right is not None:
            self.label_right.set_style_text_color(lv_theme.CONT_ITEM_SUB_FG, 0)
        if hasattr(self, "bot_line") and self.bot_line is not None:
            self.bot_line.set_style_line_color(lv_theme.CONT_ITEM_BLINE, 0)
        if left_img_src is not None and hasattr(self, "icon") and self.icon is not None:
            self.icon.set_src(left_img_src)
