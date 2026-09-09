from trezor import utils
from trezor.utils import lcd_resume

from ..i18n import gettext as _, keys as i18n_keys
from . import (
    font_GeistMono28,
    font_GeistRegular30,
    font_GeistSemiBold26,
    font_GeistSemiBold48,
    lv_theme,
    theme_path_png,
)
from .common import AnimScreen, FullSizeWindow, lv
from .components.container import ContainerFlexCol, ContainerGrid
from .components.keyboard import MnemonicKeyboard
from .components.listitem import ListItemWithLeadingCheckbox
from .components.radio import RadioTrigger
from .widgets.style import StyleWrapper


class WordEnter(FullSizeWindow):
    def __init__(self, title: str, is_slip39: bool = False):
        super().__init__(title, None, anim_dir=0)
        self.add_nav_back()
        self.title.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold26)
            .text_color(lv_theme.DT_TITLE_FG)
            .text_align_left()
            .text_letter_space(-1),
            0,
        )
        self.keyboard = MnemonicKeyboard(self, is_slip39)
        self.keyboard.ta.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
        self.keyboard.add_event_cb(self.on_ready, lv.EVENT.READY, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.submitted = False

    #     self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    # def on_nav_back(self, event_obj):
    #     code = event_obj.code
    #     if code == lv.EVENT.GESTURE:
    #         _dir = lv.indev_get_act().get_gesture_dir()
    #         if _dir == lv.DIR.RIGHT:
    #             lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def on_ready(self, _event_obj):
        if self.submitted:
            return
        input = self.keyboard.ta.get_text()
        if input == "":
            return
        self.submitted = True
        self.channel.publish(input)
        self.destroy(1000)

    def clear_input(self):
        self.keyboard.ta.set_text("")

    def show_tips(self):
        self.keyboard.tip_submitted()

    def on_nav_back(self, event_obj):
        target = event_obj.get_target()
        if target == self.nav_back.nav_btn:
            self.channel.publish(0)
            self.destroy(400)


class SelectWordCounter(FullSizeWindow):
    def __init__(self, title: str, optional_str: str):
        super().__init__(
            title, _(i18n_keys.SUBTITLE__DEVICE_RECOVER_READY_TO_RESTORE), anim_dir=0
        )
        # self.add_nav_back_right()
        self.add_nav_back()
        self.choices = RadioTrigger(
            self, optional_str, item_padding=15, item_radius=12, inteval_line=False
        )
        self.add_event_cb(self.on_ready, lv.EVENT.READY, None)
        self.add_event_cb(self.on_back, lv.EVENT.CLICKED, None)

    #     self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    # def on_nav_back(self, event_obj):
    #     code = event_obj.code
    #     if code == lv.EVENT.GESTURE:
    #         _dir = lv.indev_get_act().get_gesture_dir()
    #         if _dir == lv.DIR.RIGHT:
    #             lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def on_ready(self, _event_obj):
        self.show_dismiss_anim()
        self.channel.publish(int(self.choices.get_selected_str().split()[0]))

    def on_back(self, event_obj):
        target = event_obj.get_target()
        if target == self.nav_back.nav_btn:
            self.channel.publish(0)
            self.show_dismiss_anim()


class InvalidMnemonic(FullSizeWindow):
    def __init__(self, mnemonics: list[str]):
        word_count = len(mnemonics)
        super().__init__(
            _(i18n_keys.INVALID_PHRASES__TITLE),
            _(i18n_keys.INVALID_PHRASES__DESC),
            icon_path=theme_path_png("danger"),
            confirm_text=_(i18n_keys.GLOBAL__START_OVER),
            anim_dir=0,
            icon_pad=10,
            nav_back=False,
        )
        # self.add_nav_back()
        self.content_area.set_style_max_height(685, 0)
        row_dsc = [60] * (int((word_count + 1) // 2))
        row_dsc.append(lv.GRID_TEMPLATE.LAST)
        # 3 columns
        col_dsc = [
            217,
            217,
            lv.GRID_TEMPLATE.LAST,
        ]
        self.container = ContainerGrid(
            self.content_area,
            row_dsc=row_dsc,
            col_dsc=col_dsc,
            align_base=self.subtitle,
            pos=(0, -10),
            pad_gap=18,
        )
        self.container.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
        self.container.set_grid_align(lv.GRID_ALIGN.SPACE_BETWEEN, lv.GRID_ALIGN.CENTER)
        word_style = (
            StyleWrapper()
            .pad_hor(0)
            .pad_ver(0)
            .radius(12)
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa(lv.OPA.COVER)
            .text_align_left()
        )
        self.container.add_style(
            StyleWrapper()
            .pad_all(0)
            .pad_bottom(30)
            .text_font(font_GeistMono28)
            .text_color(lv_theme.CONT_ITEM_FG),
            0,
        )
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.content_area.set_scroll_dir(lv.DIR.VER)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_MOMENTUM)
        half = (word_count + 1) // 2
        self.words = []
        for i in range(word_count):
            col = 0 if i < half else 1
            row = i % half
            word = lv.obj(self.container)
            word.remove_style_all()
            word.add_style(word_style, 0)
            word_label = lv.label(word)
            word_label.set_align(lv.ALIGN.LEFT_MID)
            word_label.set_text("")

            word_index = lv.label(word_label)
            word_index.set_text(f" {i+1}")  # {i+1:>2}.
            word_index.add_style(
                StyleWrapper().text_color(lv_theme.CONT_ITEM_SUB_FG), 0
            )
            word_body = lv.label(word_label)
            word_body.set_text(f"{mnemonics[i]}")  # {i+1:>2}.
            word_body.add_style(StyleWrapper().text_font(font_GeistRegular30), 0)
            word_body.align_to(word_index, lv.ALIGN.OUT_RIGHT_MID, 10, 0)

            word_label.set_grid_cell(
                lv.GRID_ALIGN.STRETCH, col, 1, lv.GRID_ALIGN.STRETCH, row, 1
            )
            word.set_grid_cell(
                lv.GRID_ALIGN.STRETCH, col, 1, lv.GRID_ALIGN.STRETCH, row, 1
            )
            word.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
            self.words.append(word)
        # self.btn_no = NormalButton(self.content_area, _(i18n_keys.GLOBAL__START_OVER))
        # self.btn_no.enable_no_bg_mode()
        # self.btn_no.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)
        # self.btn_no.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.BTN_CANCEL_BG)
        #     .text_color(lv_theme.BTN_CANCEL_FG)
        #     ,0
        # )
        # self.content_area.add_style(
        #     StyleWrapper()
        #     .pad_bottom(20)
        #     ,0
        # )
        self.container.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

    def on_click(self, event_obj):
        target = event_obj.get_target()
        for i, word in enumerate(self.words):
            if word == target:
                self.show_dismiss_anim()
                self.channel.publish(i)
                break

    # def on_nav_back(self, event_obj):
    #     code = event_obj.code
    #     if code == lv.EVENT.GESTURE:
    #         _dir = lv.indev_get_act().get_gesture_dir()
    #         if _dir == lv.DIR.RIGHT:
    #             lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if lcd_resume():
                return
            if target == self.btn_yes:
                self.show_dismiss_anim()
                self.channel.publish(None)
            # elif target in (self.nav_back, self.nav_back.nav_btn):
            #     self.show_dismiss_anim()
            #     self.channel.publish(0)


class ShowTiNumber(AnimScreen):
    CODE_LEN = 4
    CELL_SIZE = 100
    CELL_GAP = 17

    def __init__(self, idx=0, number=0, prev_scr=None):
        super().__init__(
            title=_(i18n_keys.TITLE__TI_DIGITAL_ENCODING),
            subtitle=_(i18n_keys.SUBTITLE__TI_STAMPING_NUMERICAL_CODE),
            prev_scr=prev_scr,
            btn_text=_(i18n_keys.BUTTON__NEXT_STEP),
            nav_back=True,
        )
        total_width = (
            self.CODE_LEN * self.CELL_SIZE + (self.CODE_LEN - 1) * self.CELL_GAP
        )
        start_x = -(total_width // 2) + self.CELL_SIZE // 2

        self.idx_lbl = lv.label(self)
        self.idx_lbl.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.INPUT_TIP_FG)
            .text_align_center(),
            0,
        )
        # self.idx_lbl.set_text(f"{idx:02d}")
        self.idx_lbl.align(lv.ALIGN.TOP_MID, 0, 130)
        self.code_cells = []
        # knum = number
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
            cell.align_to(self.idx_lbl, lv.ALIGN.OUT_BOTTOM_MID, x_offset, 20)

            lbl = lv.label(cell)
            lbl.add_style(
                StyleWrapper()
                .text_font(font_GeistSemiBold48)
                .text_color(lv_theme.KEYBOARD_KEY_FG)
                .text_align_center(),
                0,
            )
            lbl.center()
            self.code_cells.append((cell, lbl))

        self.set_number(idx, number)
        # for i in range(self.CODE_LEN):
        #     lbl = self.code_cells[self.CODE_LEN-1-i][1]
        #     lbl.set_text(f"{knum%10}")
        #     knum = knum // 10
        self.subtitle.align_to(self.code_cells[0][0], lv.ALIGN.OUT_BOTTOM_LEFT, 0, 20)
        self.subtitle.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)
        self.btn.enable()

    def on_click(self, target):
        if target == self.btn:
            self.channel.publish(True)
            # if self.prev_scr is not None:

    def cb_nva_back_event(self):
        self.channel.publish(False)
        if self.prev_scr is not None:
            self.load_screen(self.prev_scr, destroy_self=True)

    def set_number(self, idx, number):
        self.idx_lbl.set_text(f"{idx:02d}")
        for i in range(self.CODE_LEN):
            lbl = self.code_cells[self.CODE_LEN - 1 - i][1]
            lbl.set_text(f"{number%10}")
            number = number // 10


class CheckTiSeedTips(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__SETUP_CREATE_ALMOST_DONE),
            _(i18n_keys.SUBTITLE__TI_CHECK_NUMERICAL_CODE),
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            # icon_path=theme_path_png("success"),
            # anim_dir=0,
        )
        self.title.set_style_text_line_space(0, 0)

        self.container = ContainerFlexCol(
            self.content_area,
            self.subtitle,
            padding_row=8,
            clip_corner=False,
        )
        self.checkbox_item = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.ITEM__I_HAVE_BACKED_UP),
            radius=12,
        )

        self.btn_yes.disable()

        self.container.add_event_cb(self.on_value_changed, lv.EVENT.VALUE_CHANGED, None)

    def on_value_changed(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.VALUE_CHANGED:
            if target == self.checkbox_item.checkbox:
                if target.get_state() & lv.STATE.CHECKED:
                    self.checkbox_item.enable_bg_color()
                    self.btn_yes.enable()
                else:
                    self.checkbox_item.enable_bg_color(False)
                    self.btn_yes.disable()


class SerialProtection(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__TI_SERIAL_SECURITY_PROTECTION),
            _(i18n_keys.SUBTITLE__TI_SERIAL_SECURITY_PROTECTION),
            confirm_text=_(i18n_keys.BUTTON__TI_USE_SERIAL_SECURITY_PROTECTION),
            cancel_text=_(i18n_keys.BUTTON__HAVENT_PROTECT),
            anim_dir=0,
            button_layout=0,
        )
        self.image = lv.img(self.content_area)
        self.image.set_src(theme_path_png("serial-security-protection"))
        self.image.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 100)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if target == self.btn_no:
                self.channel.publish(2)
                self.show_dismiss_anim()
                return
        super().eventhandler(event_obj)
