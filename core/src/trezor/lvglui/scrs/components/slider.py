from trezor import motor
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import font_GeistSemiBold30, lv, lv_theme, theme_path_default, theme_path_png
from ..widgets.style import StyleWrapper

MAX_VISIBLE_VALUE = 184
MIN_VISIBLE_VALUE = 16


class Slider(lv.slider):
    SLIDER_DEFAULT_ARROW_IMG_SRC = theme_path_png("slider-arrow-white")
    SLIDER_DEFAULT_DONE_IMG_SRC = theme_path_default("tools_slider-done-white.png")
    # SLIDER_DISABLE_ARROW_IMG_SRC = theme_path_default("prompt_slider-arrow-disable.png")
    # SLIDER_ARROW_WHITE_IMG_SRC = theme_path_default("prompt_slider-arrow-white.png")
    # SLIDER_DONE_WHITE_IMG_SRC = theme_path_default("prompt_slider-done-white.png")

    def __init__(
        self,
        parent,
        text,
        relative_y=-100,
        primary_color=None,
    ) -> None:
        super().__init__(parent)
        if primary_color is None:
            primary_color = lv_theme.SLIDER_NODE_FG
        self.remove_style_all()
        self.disable = False
        self._is_pressing = False
        self.primary_color = primary_color
        self.arrow_img_src = Slider.SLIDER_DEFAULT_ARROW_IMG_SRC
        self.done_img_src = Slider.SLIDER_DEFAULT_DONE_IMG_SRC
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_flag(lv.obj.FLAG.ADV_HITTEST)
        self.align(lv.ALIGN.BOTTOM_MID, 0, relative_y)
        self.set_range(0, 200)
        self.set_value(MIN_VISIBLE_VALUE, lv.ANIM.OFF)
        self.set_style_anim_time(100, lv.PART.MAIN)
        self.add_style(StyleWrapper().text_color(lv_theme.SLIDER_BG), 0)
        self.add_style(
            StyleWrapper()
            .min_height(80)
            .bg_color(lv_theme.SLIDER_BG)
            .bg_opa()
            .pad_hor(8)
            .pad_ver(2)
            .border_width(1)
            .text_color(lv_theme.SLIDER_FG)
            .radius(40),
            lv.PART.MAIN | lv.STATE.DEFAULT,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(primary_color)
            .bg_opa()
            .width(72)
            .height(72)
            .pad_all(-4)
            .text_color(lv_theme.SLIDER_FG)
            .radius(lv.RADIUS.CIRCLE),
            lv.PART.KNOB | lv.STATE.DEFAULT,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.SLIDER_BG)
            .bg_opa(lv.OPA.COVER)
            .text_color(lv_theme.SLIDER_FG)
            .radius(40),
            lv.PART.INDICATOR | lv.STATE.DEFAULT,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.SLIDER_BG)
            .bg_opa(lv.OPA.COVER)
            .text_color(lv_theme.SLIDER_FG)
            .radius(0),
            lv.PART.INDICATOR | lv.STATE.PRESSED,
        )
        self.text = text

        self.tips = lv.label(self)
        self.tips.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold30)
            .text_letter_space(-1)
            .text_color(lv_theme.SLIDER_FG),
            0,
        )
        self.tips.set_text(_(i18n_keys.BUTTON__PROCESSING))
        self.tips.center()
        self.tips.add_flag(lv.obj.FLAG.HIDDEN)
        self.arrow = lv.img(self)
        self.arrow.set_src(theme_path_png("arrow_right_3"))
        self.arrow.align_to(self.tips, lv.ALIGN.OUT_RIGHT_MID, 60, 0)

        self.add_event_cb(self.on_event, lv.EVENT.PRESSING, None)
        self.add_event_cb(self.on_event, lv.EVENT.PRESSED, None)
        self.add_event_cb(self.on_event, lv.EVENT.RELEASED, None)
        self.add_event_cb(self.on_event, lv.EVENT.DRAW_PART_BEGIN, None)
        self.add_event_cb(self.on_event, lv.EVENT.DRAW_PART_END, None)

    def _knob_reaches_arrow(self, value):
        value = max(MIN_VISIBLE_VALUE, min(value, MAX_VISIBLE_VALUE))
        knob_center_x = value * self.get_width() // 200
        knob_right_x = knob_center_x + 72 // 2
        return knob_right_x >= self.arrow.get_x()

    def _update_arrow_visibility(self, value):
        if self._is_pressing and self._knob_reaches_arrow(value):
            self.arrow.add_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.arrow.clear_flag(lv.obj.FLAG.HIDDEN)

    def enable(self, enable: bool = True):
        if enable:
            self.disable = False
            self.set_style_bg_color(lv_theme.SLIDER_BG, lv.PART.MAIN | lv.STATE.DEFAULT)
            # self.set_style_bg_color(
            #     self.primary_color
            #     , lv.PART.INDICATOR | lv.STATE.DEFAULT
            # )
            # self.arrow_img_src = Slider.SLIDER_ARROW_BLACK_IMG_SRC
            # self.done_img_src = Slider.SLIDER_DONE_WHITE_IMG_SRC
            self.set_style_bg_color(self.primary_color, lv.PART.KNOB | lv.STATE.DEFAULT)
            # self.set_style_border_color(lv_colors.UKEY_O_GRAY, 0)
            self.tips.set_style_text_color(lv_theme.SLIDER_FG, 0)
        else:
            self.disable = True
            self.set_style_bg_color(
                lv_theme.SLIDER_NODE_DFG, lv.PART.KNOB | lv.STATE.DEFAULT
            )
            self.set_style_bg_color(lv_theme.SLIDER_BG, lv.PART.MAIN | lv.STATE.DEFAULT)
            self.set_style_bg_color(
                lv_theme.SLIDER_BG, lv.PART.INDICATOR | lv.STATE.DEFAULT
            )
            # self.set_style_border_color(lv_colors.UKEY_O_GRAY_1, 0)
            self.tips.set_style_text_color(lv_theme.SLIDER_FG, 0)

    def change_knob_style(self, level):
        if level == 1:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.APP_WARNING_BG),
                lv.PART.KNOB | lv.STATE.DEFAULT,
            )
            # self.arrow_img_src = "A:/res/slide-arrow-black.png"
            # self.done_img_src = "A:/res/slider-done-black.png"
        elif level == 2:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.APP_ERROR_BG),
                lv.PART.KNOB | lv.STATE.DEFAULT,
            )

    def on_event(self, event):
        code = event.code
        target = event.get_target()
        current_value = target.get_value()
        if code == lv.EVENT.PRESSED:
            self._is_pressing = True
            self._update_arrow_visibility(current_value)
            motor.vibrate(motor.WHISPER)
        elif code == lv.EVENT.PRESSING:
            self._is_pressing = True
            if current_value > MAX_VISIBLE_VALUE:
                self.set_value(MAX_VISIBLE_VALUE, lv.ANIM.OFF)
            elif current_value < MIN_VISIBLE_VALUE:
                self.set_value(MIN_VISIBLE_VALUE, lv.ANIM.OFF)
            self._update_arrow_visibility(current_value)
        elif code == lv.EVENT.RELEASED:
            self._is_pressing = False
            if current_value < MAX_VISIBLE_VALUE:
                motor.vibrate(motor.ERROR)
                self.set_value(MIN_VISIBLE_VALUE, lv.ANIM.ON)
                self.arrow.clear_flag(lv.obj.FLAG.HIDDEN)
        elif code == lv.EVENT.DRAW_PART_BEGIN:
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())
            if dsc.part == lv.PART.KNOB:
                if dsc.id == 0:
                    if current_value < MAX_VISIBLE_VALUE:
                        # if self.disable:
                        #     dsc.rect_dsc.bg_img_src = (
                        #         Slider.SLIDER_DISABLE_ARROW_IMG_SRC
                        #     )
                        # else:
                        dsc.rect_dsc.bg_img_src = self.arrow_img_src
                        self._update_arrow_visibility(current_value)
                    else:
                        self.tips.clear_flag(lv.obj.FLAG.HIDDEN)
                        dsc.rect_dsc.bg_img_src = self.done_img_src
                        self.arrow.add_flag(lv.obj.FLAG.HIDDEN)
                        if self.has_flag(lv.obj.FLAG.CLICKABLE):
                            self.clear_flag(lv.obj.FLAG.CLICKABLE)
                        else:
                            return
                        motor.vibrate(motor.SUCCESS)
                        lv.event_send(self, lv.EVENT.READY, None)
                        # self.add_style(
                        #     StyleWrapper()
                        #     .bg_color(self.primary_color)
                        #     .bg_opa(lv.OPA.COVER)
                        #     ,lv.PART.INDICATOR | lv.STATE.PRESSED,
                        # )
                        # self.add_style(
                        #     StyleWrapper()
                        #     .bg_color(self.primary_color)
                        #     .bg_opa(lv.OPA.COVER)
                        #     ,lv.PART.INDICATOR | lv.STATE.DEFAULT,
                        # )
                        # import time
                        # time.sleep(100)
        elif code == lv.EVENT.DRAW_PART_END:
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())
            if dsc.part == lv.PART.MAIN:
                label_text = self.text
                label_size = lv.point_t()
                lv.txt_get_size(
                    label_size,
                    label_text,
                    font_GeistSemiBold30,
                    0,
                    8,
                    300,
                    lv.label.LONG.WRAP,
                )
                label_area = lv.area_t()
                label_area.x1 = (
                    dsc.draw_area.x1 + dsc.draw_area.get_width() // 2 - 150  # 300/2
                )
                label_area.x2 = label_area.x1 + 300
                label_area.y1 = dsc.draw_area.y1 + (80 - label_size.y) // 2
                label_area.y2 = label_area.y1 + label_size.y
                label_draw_dsc = lv.draw_label_dsc_t()
                label_draw_dsc.init()
                label_draw_dsc.color = (
                    lv_theme.SLIDER_FG if self.disable else lv_theme.SLIDER_FG
                )
                label_draw_dsc.font = font_GeistSemiBold30
                label_draw_dsc.align = lv.TEXT_ALIGN.CENTER
                dsc.draw_ctx.label(label_draw_dsc, label_area, label_text, None)
