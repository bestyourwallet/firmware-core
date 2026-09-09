from storage import device
from trezor import motor, utils
from trezor.crypto import bip39, random, slip39
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import (
    font_GeistRegular20,
    font_GeistRegular26,
    font_GeistSemiBold30,
    font_GeistSemiBold38,
    font_GeistSemiBold48,
    lv,
    lv_theme,
    theme_path_png,
)
from ..widgets.style import StyleWrapper
from .banner import Banner, BannerType
from .transition import BtnClickTransition

# from .transition import DefaultTransition


def compute_mask(text: str) -> int:
    mask = 0
    for c in text:
        shift = ord(c) - 97  # ord('a') == 97
        if shift < 0:
            continue
        mask |= 1 << shift
    return mask


def change_key_bg(
    dsc: lv.obj_draw_part_dsc_t,
    del_btn: int,
    etr_btn: int,
    input_len: int,
    del_range: tuple[int, int | None],
    etr_range: tuple[int, int | None],
) -> None:
    if dsc.id in (del_btn, etr_btn):
        dsc.label_dsc.font = font_GeistSemiBold48
    if dsc.id == del_btn:
        if input_len >= del_range[0] and (
            del_range[1] is None or input_len <= del_range[1]
        ):
            dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_DEL_BG
            dsc.label_dsc.color = lv_theme.KEYBOARD_DEL_FG
        else:
            dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_DEL_DBG
            dsc.label_dsc.color = lv_theme.KEYBOARD_DEL_DFG
    elif dsc.id == etr_btn:
        if input_len >= etr_range[0] and (
            etr_range[1] is None or input_len <= etr_range[1]
        ):
            dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_ETR_BG
            dsc.label_dsc.color = lv_theme.KEYBOARD_ETR_FG
        else:
            dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_ETR_DBG
            dsc.label_dsc.color = lv_theme.KEYBOARD_ETR_DFG
    # if enabled:
    #     if dsc.id == del_btn:
    #         dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_DEL_BG
    #     elif dsc.id == etr_btn:
    #         if all_enabled:
    #             dsc.rect_dsc.bg_color = lv_colors.UKEY_GREEN_1
    #             dsc.label_dsc.color = lv_colors.BLACK
    #         else:
    #             dsc.rect_dsc.bg_color = lv_colors.UKEY_O_BLACK_1
    #             dsc.label_dsc.color = lv_colors.UKEY_O_GRAY_1
    # elif dsc.id == etr_btn and allow_empty:
    #     dsc.rect_dsc.bg_color = lv_colors.KEYBOARD_ETR_BG
    #     dsc.label_dsc.color = lv_colors.KEYBOARD_ETR_FG
    # else:
    #     if dsc.id in (del_btn, etr_btn):
    #         dsc.rect_dsc.bg_color = lv_colors.UKEY_WHITE_1
    #         if dsc.id == etr_btn:
    #             dsc.label_dsc.color = (
    #                 lv_colors.UKEY_O_GRAY_1 if not allow_empty else lv_colors.BLACK
    #             )


class MnemonicKeyboard(lv.keyboard):
    """character keyboard with textarea."""

    def __init__(
        self,
        parent,
        is_slip39: bool = False,
        desc: str | None = None,
        desc_type=BannerType.Danger,
    ):
        super().__init__(parent)
        self.parent = parent
        self.is_slip39 = is_slip39
        self.ta = lv.textarea(parent)
        self.ta.align(lv.ALIGN.TOP_LEFT, 12, 177)
        self.ta.set_size(450, lv.SIZE.CONTENT)
        self.ta.add_style(
            StyleWrapper()
            .border_width(0)
            .border_color(lv_theme.INPUT_BOARDER_FG)
            .radius(22)
            .min_height(210)
            .pad_all(24)
            .bg_color(lv_theme.INPUT_BG)
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.INPUT_FG)
            .text_align_left(),
            0,
        )
        self.ta.set_max_length(11)
        self.ta.set_one_line(True)
        self.ta.set_accepted_chars("abcdefghijklmnopqrstuvwxyz")
        self.ta.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.ta.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.remove_style_all()
        self.btnm_map = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "\n",
            " ",
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            " ",
            "\n",
            lv.SYMBOL.BACKSPACE,
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            lv.SYMBOL.OK,
            "",
        ]
        self.keys = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "",  # ignore placeholder
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            "",  # ignore placeholder
            "",  # ignore backspace
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            "READY",
        ]
        self.ctrl_map = [
            lv.btnmatrix.CTRL.NO_REPEAT
            | lv.btnmatrix.CTRL.CLICK_TRIG
            | lv.btnmatrix.CTRL.POPOVER
        ] * 10
        self.ctrl_map.append(2 | lv.btnmatrix.CTRL.HIDDEN)
        self.ctrl_map.extend(
            [
                7
                | lv.btnmatrix.CTRL.NO_REPEAT
                | lv.btnmatrix.CTRL.POPOVER
                | lv.btnmatrix.CTRL.CLICK_TRIG
                | lv.btnmatrix.CTRL.POPOVER
            ]
            * 9
        )

        self.ctrl_map.append(2 | lv.btnmatrix.CTRL.HIDDEN)
        self.ctrl_map.extend(
            [4 | lv.btnmatrix.CTRL.DISABLED | lv.btnmatrix.CTRL.CLICK_TRIG]
        )
        self.ctrl_map.extend(
            [
                3
                | lv.btnmatrix.CTRL.NO_REPEAT
                | lv.btnmatrix.CTRL.POPOVER
                | lv.btnmatrix.CTRL.CLICK_TRIG
                | lv.btnmatrix.CTRL.POPOVER
            ]
            * 7
        )
        self.ctrl_map.extend(
            [
                4
                | lv.btnmatrix.CTRL.NO_REPEAT
                | lv.btnmatrix.CTRL.DISABLED
                | lv.btnmatrix.CTRL.CLICK_TRIG
            ]
        )
        self.dummy_ctl_map = []
        self.dummy_ctl_map.extend(self.ctrl_map)
        # delete button
        self.dummy_ctl_map[21] &= self.dummy_ctl_map[21] ^ lv.btnmatrix.CTRL.DISABLED
        self.set_map(lv.keyboard.MODE.TEXT_LOWER, self.btnm_map, self.ctrl_map)
        self.set_mode(lv.keyboard.MODE.TEXT_LOWER)
        self.set_width(lv.pct(100))

        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_BG)
            .text_font(font_GeistSemiBold30)
            .pad_gap(2)
            .pad_top(8)
            .pad_bottom(1)
            .height(229),
            0,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_BG)
            .bg_opa()
            .text_font(font_GeistSemiBold30)
            .text_color(lv_theme.KEYBOARD_KEY_FG)
            .radius(22),
            lv.PART.ITEMS | lv.STATE.DEFAULT,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_PBG)
            .text_color(lv_theme.KEYBOARD_KEY_PFG),
            lv.PART.ITEMS | lv.STATE.PRESSED,
        )
        self.add_style(
            StyleWrapper()
            .bg_grad_color(lv_theme.KEYBOARD_KEY_DBG)
            .text_color(lv_theme.KEYBOARD_KEY_DFG),
            lv.PART.ITEMS | lv.STATE.DISABLED,
        )
        # self.set_height(229)
        self.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        self.set_popovers(True)
        self.set_textarea(self.ta)
        self.add_event_cb(self.event_cb, lv.EVENT.PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.LONG_PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.DRAW_PART_BEGIN, None)
        self.add_event_cb(self.event_cb, lv.EVENT.VALUE_CHANGED, None)
        self.mnemonic_prompt = lv.obj(parent)
        self.mnemonic_prompt.set_size(lv.pct(100), 74)
        self.mnemonic_prompt.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.mnemonic_prompt.align_to(self, lv.ALIGN.OUT_TOP_LEFT, 0, 0)
        self.mnemonic_prompt.add_style(
            StyleWrapper()
            .border_width(0)
            .bg_color(lv_theme.KEYBOARD_TIP_BG)
            .pad_hor(1)
            .pad_ver(4)
            .bg_opa()
            .radius(10)
            .pad_column(2),
            0,
        )
        self.mnemonic_prompt.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.mnemonic_prompt.set_flex_align(
            lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.END
        )
        self.mnemonic_prompt.set_scrollbar_mode(lv.SCROLLBAR_MODE.ACTIVE)
        self.mnemonic_prompt.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        self.mnemonic_prompt.add_event_cb(self.on_click, lv.EVENT.PRESSED, None)
        self.move_foreground()
        self.vibrated = False
        if desc:
            self.banner = Banner(
                parent,
                desc_type,
                desc,
            )
            self.banner.align_to(self, lv.ALIGN.OUT_TOP_MID, 0, -10)

    def tip_submitted(self):
        self.tip_panel = lv.obj(self.parent)
        self.tip_panel.remove_style_all()
        self.tip_panel.set_size(lv.pct(80), lv.SIZE.CONTENT)
        self.tip_img = lv.img(self.tip_panel)
        self.tip_img.set_align(lv.ALIGN.LEFT_MID)
        self.tip_img.set_src(theme_path_png("feedback-correct"))
        self.tip = lv.label(self.tip_panel)
        self.tip.set_recolor(True)
        self.tip.align_to(self.tip_img, lv.ALIGN.OUT_RIGHT_MID, 4, 0)
        self.tip_panel.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular26)
            .text_color(lv_theme.APP_CORRECT_FG)
            .text_align_left(),
            0,
        )
        self.tip_panel.align_to(self.ta, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 24)
        self.tip.set_text(f"{_(i18n_keys.MSG__SUBMITTED)}")

    def on_click(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.PRESSED:
            motor.vibrate()
            return
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            child = target.get_child(0)
            if isinstance(child, lv.label):
                text = child.get_text()
                if text:
                    self.ta.set_text(text)
                self.mnemonic_prompt.clean()
                for i, key in enumerate(self.keys):
                    if key:
                        self.dummy_ctl_map[i] |= lv.btnmatrix.CTRL.DISABLED
                self.dummy_ctl_map[-1] &= (
                    self.dummy_ctl_map[-1] ^ lv.btnmatrix.CTRL.DISABLED
                )
                self.completed = True
                self.set_map(
                    lv.keyboard.MODE.TEXT_LOWER, self.btnm_map, self.dummy_ctl_map
                )
                lv.event_send(self, lv.EVENT.READY, None)

    def event_cb(self, event):
        code = event.code
        target = event.get_target()
        if code == lv.EVENT.PRESSED:
            if isinstance(target, lv.keyboard):
                btn_id = target.get_selected_btn()
                if btn_id == lv.BTNMATRIX_BTN.NONE or target.has_btn_ctrl(
                    btn_id, lv.btnmatrix.CTRL.DISABLED
                ):
                    return
                motor.vibrate()
                self.vibrated = True
            return
        elif code == lv.EVENT.LONG_PRESSED:
            self.vibrated = False
        if code == lv.EVENT.DRAW_PART_BEGIN:
            txt_input = self.ta.get_text()
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())
            change_key_bg(dsc, 21, 29, len(txt_input), (1, None), (1, None))
            # if len(txt_input) > 0:
            #     change_key_bg1(dsc, 21, 29, True, self.completed)
            # else:
            #     change_key_bg1(dsc, 21, 29, False)
            # if dsc.id in (10, 20):
            #     dsc.rect_dsc.bg_color = lv_colors.BLACK
        elif code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            if isinstance(target, lv.keyboard) and not self.vibrated:
                btn_id = target.get_selected_btn()
                if btn_id == 21:
                    motor.vibrate()
            # btn_id = event.target.get_selected_btn()
            # text = event.target.get_btn_text(btn_id)
            # if text == " ":
            #     if btn_id in (10, 21):
            #         event.target.set_selected_btn(btn_id + 1)
            #     return
            self.mnemonic_prompt.clean()
            txt_input = self.ta.get_text()
            if len(txt_input) > 0:
                words = (
                    bip39.complete_word(txt_input)
                    if not self.is_slip39
                    else slip39.complete_word(txt_input)
                ) or ""
                mask = (
                    bip39.word_completion_mask(txt_input)
                    if not self.is_slip39
                    else slip39.word_completion_mask(txt_input)
                )
                candidates = words.rstrip().split() if words else []
                btn_style_default = (
                    StyleWrapper()
                    .bg_color(lv_theme.KEYBOARD_KEY_BG)
                    .bg_opa()
                    .pad_all(16)
                    .radius(22)
                    .text_font(font_GeistSemiBold30)
                    .text_color(lv_theme.KEYBOARD_KEY_FG)
                )
                btn_style_pressed = (
                    StyleWrapper()
                    .bg_color(lv_theme.KEYBOARD_KEY_PBG)
                    .bg_opa()
                    .text_color(lv_theme.KEYBOARD_KEY_PFG)
                    .transform_height(-2)
                    .transform_width(-2)
                    .transition(BtnClickTransition())
                )
                for candidate in candidates:
                    btn = lv.btn(self.mnemonic_prompt)
                    btn.remove_style_all()
                    btn.add_style(btn_style_default, 0)
                    btn.add_style(btn_style_pressed, lv.PART.MAIN | lv.STATE.PRESSED)
                    btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
                    label = lv.label(btn)
                    label.set_text(candidate)
                for i, key in enumerate(self.keys):
                    if key and compute_mask(key) & mask:
                        self.dummy_ctl_map[i] &= (
                            self.dummy_ctl_map[i] ^ lv.btnmatrix.CTRL.DISABLED
                        )
                    else:
                        if key:
                            self.dummy_ctl_map[i] |= lv.btnmatrix.CTRL.DISABLED
                if txt_input in candidates:
                    self.dummy_ctl_map[-1] &= (
                        self.dummy_ctl_map[-1] ^ lv.btnmatrix.CTRL.DISABLED
                    )
                    self.completed = True
                else:
                    self.completed = False
                self.set_map(
                    lv.keyboard.MODE.TEXT_LOWER, self.btnm_map, self.dummy_ctl_map
                )
            else:
                self.set_map(lv.keyboard.MODE.TEXT_LOWER, self.btnm_map, self.ctrl_map)


class NumberKeyboard(lv.keyboard):
    """number keyboard with textarea."""

    def __init__(
        self,
        parent,
        max_len: int = 50,
        min_len: int = 4,
        desc: str | None = None,
        desc_type=BannerType.Danger,
        hide_ta=False,
    ) -> None:
        super().__init__(parent)
        self.hide_ta = hide_ta
        self.ta = lv.textarea(parent)
        self.ta.align(lv.ALIGN.TOP_MID, 0, 218)
        self.remove_style_all()
        self.ta.add_style(
            StyleWrapper()
            .bg_opa(lv.OPA.TRANSP)
            .border_width(0)
            .width(lv.SIZE.CONTENT)
            .max_width(432)
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.INPUT_FG)
            .text_letter_space(6)
            .text_align_center(),
            0,
        )
        self.parent = parent
        self.ta.set_one_line(True)
        self.ta.set_accepted_chars("0123456789")
        self.ta.set_max_length(max_len)
        if not hide_ta:
            self.ta.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.parent = parent
        self.max_len = max_len
        self.min_len = min_len
        self.ta.set_password_mode(True)
        self.ta.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.ta.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.nums = [i for i in range(10)]
        if device.is_random_pin_map_enabled():
            random.shuffle(self.nums)
        self.btnm_map = [
            str(self.nums[1]),
            str(self.nums[2]),
            str(self.nums[3]),
            "\n",
            str(self.nums[4]),
            str(self.nums[5]),
            str(self.nums[6]),
            "\n",
            str(self.nums[7]),
            str(self.nums[8]),
            str(self.nums[9]),
            "\n",
            lv.SYMBOL.BACKSPACE,
            str(self.nums[0]),
            lv.SYMBOL.OK,
            "",
        ]
        self.dummy_btnm_map = [
            str(self.nums[1]),
            str(self.nums[2]),
            str(self.nums[3]),
            "\n",
            str(self.nums[4]),
            str(self.nums[5]),
            str(self.nums[6]),
            "\n",
            str(self.nums[7]),
            str(self.nums[8]),
            str(self.nums[9]),
            "\n",
            lv.SYMBOL.CLOSE,
            str(self.nums[0]),
            lv.SYMBOL.OK,
            "",
        ]
        self.ctrl_map = [
            lv.btnmatrix.CTRL.NO_REPEAT
            | lv.btnmatrix.CTRL.CLICK_TRIG
            | lv.btnmatrix.CTRL.POPOVER
        ] * 12
        for i in (9, 11):
            self.ctrl_map[i] = (
                lv.btnmatrix.CTRL.NO_REPEAT
                | lv.btnmatrix.CTRL.DISABLED
                | lv.btnmatrix.CTRL.CLICK_TRIG
                | lv.btnmatrix.CTRL.POPOVER
            )
        self._show_empty_input_map()
        self.set_mode(lv.keyboard.MODE.NUMBER)
        self.set_size(lv.pct(100), 400)

        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_BG)
            .pad_hor(15)
            .pad_ver(10)
            .pad_gap(15),
            0,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_BG)
            .radius(22)
            .width(140)
            .bg_opa(lv.OPA.COVER)
            # .height(80)
            .text_color(lv_theme.KEYBOARD_KEY_FG).text_font(font_GeistSemiBold48),
            lv.PART.ITEMS | lv.STATE.DEFAULT,
        )
        self.add_style(StyleWrapper(), 0)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_PBG)
            .text_color(lv_theme.KEYBOARD_KEY_PFG)
            .bg_opa(lv.OPA._80)
            # .transform_height(-2)
            # .transform_width(-2)
            # .transition(DefaultTransition())
            ,
            lv.PART.ITEMS | lv.STATE.PRESSED,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_DBG)
            .text_color(lv_theme.KEYBOARD_KEY_DFG)
            .bg_opa(lv.OPA.COVER),
            lv.PART.ITEMS | lv.STATE.DISABLED,
        )

        self.set_popovers(True)
        self.align(lv.ALIGN.BOTTOM_MID, 0, -4)
        self.set_textarea(self.ta)
        self.input_count_tips = lv.obj(parent)
        self.input_count_tips.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
        self.input_count_tips.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP).border_width(0),
            0,
        )
        self.input_count_tips1 = lv.label(self.input_count_tips)
        self.input_count_tips1.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_letter_space(1)
            .text_color(lv_theme.INPUT_FG),
            0,
        )
        self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)
        self.input_count_tips2 = lv.label(self.input_count_tips)
        self.input_count_tips2.align(lv.ALIGN.OUT_RIGHT_MID, 0, 0)
        self.input_count_tips2.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_letter_space(1)
            .text_color(lv_theme.INPUT_TIP_FG),
            0,
        )
        if self.hide_ta:
            self.ta.add_flag(lv.obj.FLAG.HIDDEN)
            self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)
        if desc:
            self.banner = Banner(
                parent,
                desc_type,
                desc,
            )
            self.banner.align_to(self, lv.ALIGN.OUT_TOP_MID, 0, -10)
        # self.input_count_tips2.add_flag(lv.obj.FLAG.HIDDEN)

        self.add_event_cb(self.event_cb, lv.EVENT.PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.LONG_PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.DRAW_PART_BEGIN, None)
        self.add_event_cb(self.event_cb, lv.EVENT.VALUE_CHANGED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.READY, None)
        self.add_event_cb(self.event_cb, lv.EVENT.CANCEL, None)
        self.previous_input_len = 0
        self.vibrated = False

    def update_count_tips(self):
        # Update/show tips only when input length exceeds the threshold.
        if self.hide_ta:
            return
        input_len = len(self.ta.get_text())
        if input_len >= (self.max_len // 5 if self.max_len != 6 else 0):
            self.input_count_tips1.set_text(f"{len(self.ta.get_text())}/")
            # self.input_count_tips1.align_to(self.ta, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.input_count_tips2.set_text(f"{self.max_len}")
            self.input_count_tips2.align_to(
                self.input_count_tips1, lv.ALIGN.OUT_RIGHT_MID, 0, 0
            )
            # if hasattr(self.parent, "subtitle"):
            #     self.input_count_tips.align_to(self.parent.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 16)
            # else:
            self.input_count_tips.align_to(self.ta, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
            if self.input_count_tips.has_flag(lv.obj.FLAG.HIDDEN):
                self.input_count_tips.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            if not self.input_count_tips.has_flag(lv.obj.FLAG.HIDDEN):
                self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)

    def _show_empty_input_map(self):
        self.dummy_ctl_map = []
        self.dummy_ctl_map.extend(self.ctrl_map)
        self.dummy_ctl_map[9] &= self.dummy_ctl_map[9] ^ lv.btnmatrix.CTRL.DISABLED
        self.set_map(lv.keyboard.MODE.NUMBER, self.dummy_btnm_map, self.dummy_ctl_map)

    def toggle_number_input_keys(self, enable: bool):
        if enable:
            self.dummy_ctl_map = []
            self.dummy_ctl_map.extend(self.ctrl_map)
            if self.input_len >= self.min_len:
                self.dummy_ctl_map[-1] &= (
                    self.dummy_ctl_map[-1] ^ lv.btnmatrix.CTRL.DISABLED
                )
            if self.input_len > 0:
                self.dummy_ctl_map[9] &= (
                    self.dummy_ctl_map[9] ^ lv.btnmatrix.CTRL.DISABLED
                )
            else:
                if self.previous_input_len > self.input_len:
                    self.ta.add_flag(lv.obj.FLAG.HIDDEN)
                self._show_empty_input_map()
                return
            self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.dummy_ctl_map)

        else:
            self.dummy_ctl_map = []
            self.dummy_ctl_map.extend(self.ctrl_map)
            for i in range(12):
                if i not in (9, 11):
                    self.dummy_ctl_map[i] |= lv.btnmatrix.CTRL.DISABLED
                else:
                    self.dummy_ctl_map[i] &= (
                        self.dummy_ctl_map[i] ^ lv.btnmatrix.CTRL.DISABLED
                    )
            self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.dummy_ctl_map)

    def event_cb(self, event):
        code = event.code
        target = event.get_target()
        if code == lv.EVENT.PRESSED:
            if isinstance(target, lv.keyboard):
                btn_id = target.get_selected_btn()
                # if normal_run:
                if btn_id == lv.BTNMATRIX_BTN.NONE or target.has_btn_ctrl(
                    btn_id, lv.btnmatrix.CTRL.DISABLED
                ):
                    return
                motor.vibrate()
                self.vibrated = True
            return
        elif code == lv.EVENT.LONG_PRESSED:
            self.vibrated = False
        input_len = len(self.ta.get_text())
        self.input_len = input_len
        if input_len > 0 and self.ta.has_flag(lv.obj.FLAG.HIDDEN):
            self.input_count_tips.clear_flag(lv.obj.FLAG.HIDDEN)
        elif input_len == 0 and not self.ta.has_flag(lv.obj.FLAG.HIDDEN):
            self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)
        if not self.hide_ta:
            self.ta.clear_flag(lv.obj.FLAG.HIDDEN)
        if code == lv.EVENT.DRAW_PART_BEGIN:
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())

            if dsc.id in (9, 11):
                change_key_bg(
                    dsc,
                    9,
                    11,
                    input_len,
                    (0 if input_len == 0 else 1, None),
                    (self.min_len, None),
                )
            # if input_len >= self.min_len:
            #     change_key_bg(dsc, 9, -1, True)
            # elif input_len > 0:
            #     change_key_bg(dsc, 9, -1, True) # , False
            # else:
            # change_key_bg(dsc, 9, -1, False)
            # if dsc.id == 9:
            #     dsc.rect_dsc.bg_color = lv_colors.UKEY_O_RED_1
            # dsc.rect_dsc.bg_img_src = theme_path_default("keyboard-close.png")
        elif code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            if isinstance(target, lv.keyboard):
                btn_id = target.get_selected_btn()
                text = target.get_btn_text(btn_id)
                if text == lv.SYMBOL.CLOSE:
                    if len(self.ta.get_text()) == 0:
                        lv.event_send(self, lv.EVENT.CANCEL, None)
                    return
                if text == lv.SYMBOL.OK:
                    if len(self.ta.get_text()) >= self.min_len:
                        lv.event_send(self, lv.EVENT.READY, None)
                    return
                if not self.vibrated and btn_id == 9:
                    motor.vibrate()
            if input_len > 10:
                self.ta.set_cursor_pos(lv.TEXTAREA_CURSOR.LAST)
            if input_len >= self.max_len:
                # disable number keys
                self.toggle_number_input_keys(False)
            elif input_len > 0:
                # enable number keys
                self.toggle_number_input_keys(True)
            else:
                self._show_empty_input_map()
            self.update_count_tips()
            self.previous_input_len = input_len
        elif code in (lv.EVENT.READY, lv.EVENT.CANCEL):
            motor.vibrate()


class IndexKeyboard(lv.keyboard):
    """number keyboard with textarea for account index."""

    def __init__(
        self,
        parent,
        max_len: int = 50,
        min_len: int = 4,
        is_pin: bool = True,
        desc: str | None = None,
        desc_type=BannerType.Danger,
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.is_pin = is_pin
        self.ta = lv.textarea(parent)
        self.ta.align(lv.ALIGN.TOP_MID, 0, 218)

        self.ta.add_style(
            StyleWrapper()
            .bg_color(lv_theme.INPUT_BG)
            .text_color(lv_theme.INPUT_FG)
            .border_width(0)
            .width(lv.SIZE.CONTENT)
            .bg_opa(255)
            .max_width(432)
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.INPUT_FG)
            .text_letter_space(6)
            .text_align_center(),
            0,
        )
        self.parent = parent
        self.ta.set_one_line(True)
        if self.is_pin:
            self.ta.set_accepted_chars("0123456789")
        else:
            self.ta.set_accepted_chars("#0123456789")
        self.ta.set_max_length(max_len)
        self.max_len = max_len
        self.min_len = min_len
        self.ta.set_password_mode(is_pin)
        self.ta.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.ta.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.nums = [i for i in range(10)]
        if device.is_random_pin_map_enabled():
            random.shuffle(self.nums)
        self.btnm_map = [
            str(self.nums[1]),
            str(self.nums[2]),
            str(self.nums[3]),
            "\n",
            str(self.nums[4]),
            str(self.nums[5]),
            str(self.nums[6]),
            "\n",
            str(self.nums[7]),
            str(self.nums[8]),
            str(self.nums[9]),
            "\n",
            lv.SYMBOL.BACKSPACE,
            str(self.nums[0]),
            lv.SYMBOL.OK,
            "",
        ]
        # self.dummy_btnm_map = [
        #     str(self.nums[1]),
        #     str(self.nums[2]),
        #     str(self.nums[3]),
        #     "\n",
        #     str(self.nums[4]),
        #     str(self.nums[5]),
        #     str(self.nums[6]),
        #     "\n",
        #     str(self.nums[7]),
        #     str(self.nums[8]),
        #     str(self.nums[9]),
        #     "\n",
        #     lv.SYMBOL.CLOSE,
        #     str(self.nums[0]),
        #     lv.SYMBOL.OK,
        #     "",
        # ]
        self.ctrl_map = [
            lv.btnmatrix.CTRL.NO_REPEAT
            | lv.btnmatrix.CTRL.CLICK_TRIG
            | lv.btnmatrix.CTRL.POPOVER
        ] * 12

        for i in [9, 11]:
            self.ctrl_map[i] = (
                lv.btnmatrix.CTRL.NO_REPEAT
                | lv.btnmatrix.CTRL.DISABLED
                | lv.btnmatrix.CTRL.CLICK_TRIG
                | lv.btnmatrix.CTRL.POPOVER
            )
        self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.ctrl_map)
        self.set_mode(lv.keyboard.MODE.NUMBER)
        self.set_size(lv.pct(100), 400)

        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_BG)
            .pad_hor(15)
            .pad_ver(10)
            .pad_gap(15),
            0,
        )
        self.add_style(
            StyleWrapper()
            .width(140)
            .height(80)
            .bg_color(lv_theme.KEYBOARD_KEY_BG)
            .radius(22)
            .bg_opa(lv.OPA.COVER)
            .text_color(lv_theme.KEYBOARD_KEY_FG)
            .text_font(font_GeistSemiBold48),
            lv.PART.ITEMS | lv.STATE.DEFAULT,
        )
        self.add_style(StyleWrapper(), 0)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_PBG)
            .text_color(lv_theme.KEYBOARD_KEY_PFG)
            .bg_opa(lv.OPA._80),
            lv.PART.ITEMS | lv.STATE.PRESSED,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_DBG)
            .text_color(lv_theme.KEYBOARD_KEY_DFG)
            .bg_opa(lv.OPA.COVER),
            lv.PART.ITEMS | lv.STATE.DISABLED,
        )

        self.set_popovers(True)
        self.align(lv.ALIGN.BOTTOM_MID, 0, -4)
        self.set_textarea(self.ta)
        if desc:
            self.banner = Banner(
                parent,
                desc_type,
                desc,
            )
            self.banner.align_to(self, lv.ALIGN.OUT_TOP_MID, 0, -10)

        # self.input_count_tips = lv.label(parent)
        # self.input_count_tips.align(lv.ALIGN.BOTTOM_MID, 0, -512)
        # self.input_count_tips.add_style(
        #     StyleWrapper()
        #     .text_font(font_GeistRegular20)
        #     .text_letter_space(1)
        #     .text_color(lv_colors.LIGHT_GRAY),
        #     0,
        # )
        # self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)

        self.add_event_cb(self.event_cb, lv.EVENT.PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.LONG_PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.DRAW_PART_BEGIN, None)
        self.add_event_cb(self.event_cb, lv.EVENT.VALUE_CHANGED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.READY, None)
        self.add_event_cb(self.event_cb, lv.EVENT.CANCEL, None)
        self.previous_input_len = 0
        self.vibrated = False

    # def update_count_tips(self):
    #     """Update/show tips only when input length larger than 10"""
    #     input_len = len(self.ta.get_text())
    #     if input_len >= (self.max_len // 5 if self.max_len != 6 else 0):
    #         self.input_count_tips.set_text(f"{len(self.ta.get_text())}/{self.max_len}")
    #         if self.input_count_tips.has_flag(lv.obj.FLAG.HIDDEN):
    #             self.input_count_tips.clear_flag(lv.obj.FLAG.HIDDEN)
    #     else:
    #         if not self.input_count_tips.has_flag(lv.obj.FLAG.HIDDEN):
    #             self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)

    def toggle_number_input_keys(self, enable: bool):
        if enable:
            self.dummy_ctl_map = []
            self.dummy_ctl_map.extend(self.ctrl_map)

            if self.is_pin:
                if self.input_len >= self.min_len:
                    self.dummy_ctl_map[-1] &= (
                        self.dummy_ctl_map[-1] ^ lv.btnmatrix.CTRL.DISABLED
                    )
            else:
                if self.input_len > 0:
                    self.dummy_ctl_map[-1] &= (
                        self.dummy_ctl_map[-1] ^ lv.btnmatrix.CTRL.DISABLED
                    )

            if self.input_len > 0 or (
                not self.is_pin and self.ta.get_text().startswith("#")
            ):
                self.dummy_ctl_map[-3] = (
                    lv.btnmatrix.CTRL.CLICK_TRIG | lv.btnmatrix.CTRL.POPOVER
                )
            else:
                self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.ctrl_map)
                return

            self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.dummy_ctl_map)
        else:
            self.dummy_ctl_map = []
            self.dummy_ctl_map.extend(self.ctrl_map)
            for i in range(12):
                if i not in (9, 11):
                    self.dummy_ctl_map[i] |= lv.btnmatrix.CTRL.DISABLED
                else:
                    self.dummy_ctl_map[i] &= (
                        self.dummy_ctl_map[i] ^ lv.btnmatrix.CTRL.DISABLED
                    )
            self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.dummy_ctl_map)

    def event_cb(self, event):
        code = event.code
        target = event.get_target()
        text = self.ta.get_text()
        if code == lv.EVENT.PRESSED:
            if isinstance(target, lv.keyboard):
                btn_id = target.get_selected_btn()
                if btn_id == lv.BTNMATRIX_BTN.NONE or target.has_btn_ctrl(
                    btn_id, lv.btnmatrix.CTRL.DISABLED
                ):
                    return
                motor.vibrate()
                self.vibrated = True
            return
        elif code == lv.EVENT.LONG_PRESSED:
            self.vibrated = False
        if not self.is_pin and text.startswith("#"):
            input_len = len(text) - 1
        else:
            input_len = len(text)
        self.input_len = input_len
        self.ta.clear_flag(lv.obj.FLAG.HIDDEN)

        if code == lv.EVENT.DRAW_PART_BEGIN:
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())
            # if self.is_pin:
            change_key_bg(
                dsc,
                9,
                11,
                input_len,
                (1, None),
                (self.min_len if self.is_pin else 1, None),
            )
            # if input_len >= self.min_len:
            #     change_key_bg1(dsc, 9, 11, True)
            # elif input_len > 0:
            #     change_key_bg1(dsc, 9, 11, True, False)
            # else:
            #     change_key_bg1(dsc, 9, 11, False)
            #     if dsc.id == 9:
            #         dsc.rect_dsc.bg_color = lv_colors.UKEY_O_RED_1
            # else:
            # change_key_bg(dsc, 9, 11, input_len, (1, None), (1, None))
            # if input_len > 0:
            #     change_key_bg1(dsc, 9, 11, True)
            # else:
            #     change_key_bg1(dsc, 9, 11, False)
            #     if dsc.id == 9:
            #         dsc.rect_dsc.bg_color = lv_colors.UKEY_O_RED_1

        elif code == lv.EVENT.VALUE_CHANGED:
            utils.lcd_resume()
            if isinstance(target, lv.keyboard) and not self.vibrated:
                btn_id = target.get_selected_btn()
                if btn_id == 9:
                    motor.vibrate()
            if not self.is_pin:
                if text and not text.startswith("#"):
                    self.ta.set_text("#" + text)
                elif text == "":
                    self.ta.set_text("")

            if input_len + 1 >= self.max_len:
                self.toggle_number_input_keys(False)
            elif input_len > 0:

                self.toggle_number_input_keys(True)
            else:
                self.set_map(lv.keyboard.MODE.NUMBER, self.btnm_map, self.ctrl_map)

            # self.update_count_tips()
            self.previous_input_len = input_len


class PassphraseKeyboard(lv.btnmatrix):
    def __init__(self, parent, max_len, min_len=0) -> None:
        super().__init__(parent)
        self.min_len = min_len
        self.ta = lv.textarea(parent)
        self.ta.align(lv.ALIGN.TOP_MID, 0, 177)
        self.ta.set_size(450, lv.SIZE.CONTENT)
        self.ta.add_style(
            StyleWrapper().bg_color(lv_theme.INPUT_BG).text_color(lv_theme.INPUT_FG)
            # .border_color(lv_theme.INPUT_BOARDER_FG)
            .bg_opa()
            .border_width(0)
            .text_font(font_GeistSemiBold38)
            .text_align_left()
            .min_height(210)
            .radius(22)
            .pad_all(24),
            0,
        )
        self.ta.set_accepted_chars(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_<>.:@/|*#\\!()+%&-[]?{},'`;\"~$^= "
        )
        self.ta.set_max_length(max_len)
        self.ta.set_cursor_click_pos(True)
        self.ta.add_state(lv.STATE.FOCUSED)
        self.ta.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.btn_map_text_lower = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "\n",
            " ",
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            " ",
            "\n",
            " ",
            "ABC",
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            " ",
            "\n",
            lv.SYMBOL.BACKSPACE,
            "123",
            " ",
            lv.SYMBOL.OK,
            "",
        ]
        self.btn_map_text_upper = [
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "\n",
            " ",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            " ",
            "\n",
            " ",
            "abc",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
            " ",
            "\n",
            lv.SYMBOL.BACKSPACE,
            "123",
            " ",
            lv.SYMBOL.OK,
            "",
        ]
        self.btn_map_text_special = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            "\n",
            " ",
            "^",
            "_",
            "[",
            "]",
            "@",
            "$",
            "%",
            "{",
            "}",
            " ",
            "\n",
            " ",
            "#*<",
            "`",
            "-",
            "/",
            ",",
            ".",
            ":",
            ";",
            " ",
            "\n",
            lv.SYMBOL.BACKSPACE,
            "abc",
            " ",
            lv.SYMBOL.OK,
            "",
        ]
        self.btn_map_text_special1 = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            "\n",
            " ",
            "!",
            "?",
            "#",
            "~",
            "&",
            '"',
            "'",
            "(",
            ")",
            " ",
            "\n",
            " ",
            "123",
            "+",
            "=",
            "<",
            ">",
            "\\",
            "|",
            "*",
            " ",
            "\n",
            lv.SYMBOL.BACKSPACE,
            "abc",
            " ",
            lv.SYMBOL.OK,
            "",
        ]
        # line1
        self.ctrl_map = [lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.POPOVER] * 10
        # line2
        self.ctrl_map.extend([3 | lv.btnmatrix.CTRL.NO_REPEAT])
        self.ctrl_map.extend(
            [7 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.POPOVER] * 9
        )
        self.ctrl_map.extend([3 | lv.btnmatrix.CTRL.NO_REPEAT])
        # line3
        self.ctrl_map.extend([2 | lv.btnmatrix.CTRL.NO_REPEAT])
        self.ctrl_map.extend(
            [7 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.CLICK_TRIG]
        )
        self.ctrl_map.extend(
            [5 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.POPOVER] * 7
        )
        self.ctrl_map.extend([4 | lv.btnmatrix.CTRL.NO_REPEAT])
        # line4
        self.ctrl_map.extend([3])
        self.ctrl_map.extend(
            [2 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.CLICK_TRIG]
        )
        self.ctrl_map.extend(
            [7 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.CLICK_TRIG]
        )
        self.ctrl_map.extend(
            [3 | lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.CLICK_TRIG]
        )
        self.set_map(self.btn_map_text_lower)
        self.set_ctrl_map(self.ctrl_map)
        self.set_size(lv.pct(100), 294)
        self.align(lv.ALIGN.BOTTOM_MID, 0, -1)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_BG)
            .border_width(0)
            .pad_all(0)
            .pad_gap(2),
            0,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_BG)
            .text_color(lv_theme.KEYBOARD_KEY_FG)
            .radius(22)
            .text_font(font_GeistSemiBold30)
            .text_letter_space(-1),
            lv.PART.ITEMS | lv.STATE.DEFAULT,
        )
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.KEYBOARD_KEY_PBG)
            .text_color(lv_theme.KEYBOARD_KEY_PFG),
            lv.PART.ITEMS | lv.STATE.PRESSED,
        )

        self.input_count_tips = lv.label(parent)
        self.input_count_tips.set_size(lv.pct(100), 38)
        self.input_count_tips.align_to(self, lv.ALIGN.OUT_TOP_MID, 0, 0)
        self.input_count_tips.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_letter_space(1)
            .pad_all(8)
            .text_align_center()
            .text_color(lv_theme.INPUT_TIP_FG),
            0,
        )

        self.update_count_tips()
        self.add_event_cb(self.event_cb, lv.EVENT.PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.LONG_PRESSED, None)
        self.add_event_cb(self.event_cb, lv.EVENT.DRAW_PART_BEGIN, None)
        self.add_event_cb(self.event_cb, lv.EVENT.VALUE_CHANGED, None)
        self.ta.add_event_cb(self.event_cb, lv.EVENT.FOCUSED, None)
        self.move_foreground()
        self.vibrated = False
        self.update_ok_button_state()

    def update_count_tips(self):
        self.input_count_tips.set_text(
            f"{len(self.ta.get_text())}/{self.ta.get_max_length()}"
        )

    def update_ok_button_state(self):
        current_text = self.ta.get_text()
        current_len = len(current_text)

        if current_len >= self.min_len:
            self.clear_btn_ctrl(34, lv.btnmatrix.CTRL.DISABLED)
            self.set_btn_ctrl(
                34, lv.btnmatrix.CTRL.NO_REPEAT | lv.btnmatrix.CTRL.CLICK_TRIG
            )
        else:
            self.set_btn_ctrl(34, lv.btnmatrix.CTRL.DISABLED)
            self.clear_btn_ctrl(34, lv.btnmatrix.CTRL.CLICK_TRIG)

    def event_cb(self, event):
        code = event.code
        target = event.get_target()
        if code == lv.EVENT.PRESSED:
            if isinstance(target, lv.btnmatrix):
                btn_id = target.get_selected_btn()
                if btn_id == lv.BTNMATRIX_BTN.NONE:
                    return
                if btn_id == 31 and len(self.ta.get_text()) == 0:
                    return
                motor.vibrate()
                self.vibrated = True
            return
        elif code == lv.EVENT.LONG_PRESSED:
            self.vibrated = False
        if code == lv.EVENT.DRAW_PART_BEGIN:
            txt_input = self.ta.get_text()
            dsc = lv.obj_draw_part_dsc_t.__cast__(event.get_param())
            change_key_bg(dsc, 31, 34, len(txt_input), (1, None), (self.min_len, None))
            # if len(txt_input) > 0:
            #     change_key_bg(dsc, 31, 34, True)
            # else:
            #     change_key_bg(dsc, 31, 34, False, allow_empty=True)

            # if dsc.id == 34:
            #     if len(txt_input) >= self.min_len:
            #         dsc.rect_dsc.bg_color = lv_colors.UKEY_O_GREEN
            #     else:
            #         dsc.rect_dsc.bg_color = lv_colors.GRAY
            if dsc.id in (10, 20, 21, 30):
                dsc.rect_dsc.bg_color = lv_theme.KEYBOARD_BG
        elif code == lv.EVENT.VALUE_CHANGED:
            if isinstance(target, lv.btnmatrix):
                utils.lcd_resume()
                btn_id = target.get_selected_btn()
                if btn_id == lv.BTNMATRIX_BTN.NONE:
                    return
                text = target.get_btn_text(btn_id)
                if text == "":
                    return
                if text == " ":
                    if btn_id in (10, 21):
                        target.set_selected_btn(btn_id + 1)
                        return
                    elif btn_id in (20, 30):
                        target.set_selected_btn(btn_id - 1)
                        return
                if text == "ABC":
                    self.set_map(self.btn_map_text_upper)
                    self.set_ctrl_map(self.ctrl_map)
                    return
                elif text == "123":
                    self.set_map(self.btn_map_text_special)
                    self.set_ctrl_map(self.ctrl_map)
                    return
                elif text == "abc":
                    self.set_map(self.btn_map_text_lower)
                    self.set_ctrl_map(self.ctrl_map)
                    return
                elif text == "#*<":
                    self.set_map(self.btn_map_text_special1)
                    self.set_ctrl_map(self.ctrl_map)
                    return
                elif text == lv.SYMBOL.BACKSPACE:
                    if len(self.ta.get_text()) == 0:
                        target.set_selected_btn(lv.BTNMATRIX_BTN.NONE)
                        return
                    self.ta.del_char()
                    self.update_count_tips()
                    self.update_ok_button_state()
                    if not self.vibrated:
                        motor.vibrate()
                    return
                elif text == lv.SYMBOL.OK:
                    if len(self.ta.get_text()) >= self.min_len:
                        lv.event_send(self, lv.EVENT.READY, None)
                    return
                # print('BUTTON_: ', text, btn_id, _(i18n_keys.BUTTON__CONFIRM))
                self.ta.add_text(text)
                self.update_count_tips()
                self.update_ok_button_state()
        elif code == lv.EVENT.FOCUSED and target == self.ta:
            utils.lcd_resume()
