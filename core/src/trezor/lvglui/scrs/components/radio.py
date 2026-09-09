from .. import font_GeistSemiBold30, lv, lv_theme
from ..widgets.style import StyleWrapper
from .container import ContainerFlexCol
from .line import Line
from .transition import DefaultTransition


class Radio:
    def __init__(self, parent, options, height=None) -> None:
        self.change_color_only = False
        self.container = ContainerFlexCol(parent, None, padding_row=0, height=height)
        self.container.add_style(StyleWrapper().bg_opa(lv.OPA.TRANSP), 0)
        self.container.add_flag(lv.obj.FLAG.SCROLLABLE)
        self.items: list[Radio.RadioItem] = []
        self.check_index = 0
        self.choices = options.split("\n")
        for idx, choice in enumerate(self.choices):
            item = Radio.RadioItem(
                self.container,
                choice,
                bot_line=True if idx != len(self.choices) - 1 else False,
            )
            if idx == 0:
                item.set_checked()
            self.items.append(item)
        self.container.add_event_cb(self.on_selected_changed, lv.EVENT.CLICKED, None)

    def on_selected_changed(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            from trezor import utils

            if utils.lcd_resume():
                return
            last_checked = self.check_index
            for idx, item in enumerate(self.items):

                if target != item and idx == last_checked:
                    item.set_uncheck(change_color_only=self.change_color_only)
                if target == item and idx != last_checked:
                    self.check_index = idx
                    item.set_checked(change_color_only=self.change_color_only)

    def set_flag(self):
        self.change_color_only = True

    def get_selected_index(self):
        return self.check_index

    def get_selected_str(self):
        return self.items[self.check_index].get_text()

    def set_style_text_font(self, font, _other):
        for item in self.items:
            item.set_style_text_font(font, 0)

    class RadioItem(lv.obj):
        def __init__(self, parent, text: str, bot_line: bool = False) -> None:
            super().__init__(parent)
            self.content = text
            self.set_size(450, 80)
            self.add_style(
                StyleWrapper()
                .bg_color(lv_theme.CONT_ITEM_BG)
                .bg_opa()
                .radius(0)
                .pad_hor(24)
                .pad_ver(0)
                .text_font(font_GeistSemiBold30)
                .text_color(lv_theme.CONT_ITEM_FG)
                .text_align_left(),
                0,
            )
            self.label = lv.label(self)
            self.label.set_long_mode(lv.label.LONG.WRAP)
            self.label.set_text(text)
            self.label.set_align(lv.ALIGN.CENTER)
            self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
            self.checked = False
            if bot_line:
                bot_line = Line(self, 420)
                # bot_line = lv.obj(self)
                # bot_line.set_size(420,1)
                # bot_line.add_style(
                #     StyleWrapper()
                #     .bg_color(lv_theme.CONT_ITEM_BLINE)
                #     .border_opa(lv.OPA.TRANSP)
                #     ,0,
                # )
                bot_line.align_to(self, lv.ALIGN.BOTTOM_MID, 0, 0)

        def set_checked(self, change_color_only: bool = False):
            if not self.checked:
                self.checked = True
                self.set_style_bg_color(lv_theme.CONT_ITEM_PBG, 0)
                self.set_style_text_color(lv_theme.CONT_ITEM_PFG, 0)
                if not change_color_only:
                    self.set_style_text_font(font_GeistSemiBold30, 0)

        def set_uncheck(self, change_color_only: bool = False):
            if self.checked:
                self.checked = False
                self.set_style_bg_color(lv_theme.CONT_ITEM_BG, 0)
                self.set_style_text_color(lv_theme.CONT_ITEM_FG, 0)
                if not change_color_only:
                    self.set_style_text_font(font_GeistSemiBold30, 0)

        def get_text(self) -> str:
            return self.content


class RadioTrigger:
    def __init__(
        self,
        parent,
        options,
        item_padding=0,
        item_radius=0,
        item_center=False,
        item_bg_color=None,
        radius=20,
        inteval_line=True,
        bg_color=None,
    ) -> None:
        if item_bg_color is None:
            item_bg_color = lv_theme.CONT_ITEM_BG
        self.parent = parent
        self.container = ContainerFlexCol(
            parent, None, padding_row=item_padding, radius=radius
        )
        if bg_color:
            self.container.add_style(
                StyleWrapper().bg_color(bg_color)  # lv_colors.UKEY_WHITE_1)
                # .pad_bottom(15)
                .bg_opa(lv.OPA.COVER),
                0,
            )
        else:
            self.container.add_style(
                StyleWrapper().pad_bottom(15).bg_opa(lv.OPA.TRANSP), 0
            )

        # self.container.align_to(parent, lv.ALIGN.BOTTOM_MID, 0, -15)
        self.items: list[RadioTrigger.RadioItem] = []
        self.check_index = 0
        self.changed = False
        self.choices = options.split("\n")
        for _idx, choice in enumerate(self.choices):
            item = RadioTrigger.RadioItem(
                self.container,
                choice,
                radius=item_radius,
                content_center=item_center,
                bg_color=item_bg_color,
                bot_line=True
                if _idx != len(self.choices) - 1 and inteval_line
                else False,
            )
            self.items.append(item)
        self.container.add_event_cb(self.on_selected_changed, lv.EVENT.CLICKED, None)

    def on_selected_changed(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            from trezor import motor, utils

            if utils.lcd_resume():
                return
            for idx, item in enumerate(self.items):
                if target == item:
                    motor.vibrate()
                    self.check_index = idx
                    self.changed = True
                    lv.event_send(self.parent, lv.EVENT.READY, None)

    def get_selected_index(self):
        return self.check_index

    def get_selected_str(self):
        return self.items[self.check_index].get_text()

    class RadioItem(lv.btn):
        def __init__(
            self,
            parent,
            text: str,
            font=font_GeistSemiBold30,
            radius=0,
            bot_line=False,
            bg_color=None,  # UKEY_GREEN_1
            content_center=False,
        ) -> None:
            super().__init__(parent)
            if bg_color is None:
                bg_color = lv_theme.CONT_ITEM_BG
            self.content = text
            self.remove_style_all()
            self.set_size(450, 80)
            self.add_style(
                StyleWrapper()
                .bg_color(bg_color)
                .bg_opa(lv.OPA.COVER)
                .radius(radius)
                .pad_hor(24)
                .pad_top(0)
                .pad_bottom(0)
                .text_font(font)
                .text_color(lv_theme.CONT_ITEM_FG)
                .text_align_left(),
                0,
            )
            self.set_style_shadow_width(0, 0)
            self.add_style(
                StyleWrapper()
                .bg_color(lv_theme.CONT_ITEM_PBG)
                .bg_opa(lv.OPA.COVER)
                .transform_height(-2)
                .transform_width(-4)
                .transition(DefaultTransition()),
                lv.PART.MAIN | lv.STATE.PRESSED,
            )
            self.label = lv.label(self)
            self.label.set_long_mode(lv.label.LONG.WRAP)
            self.label.set_text(text)
            self.label.set_align(lv.ALIGN.LEFT_MID)
            if content_center:
                self.label.set_size(450, lv.SIZE.CONTENT)
                self.label.add_style(StyleWrapper().text_align_center(), 0)
                self.add_style(StyleWrapper().pad_hor(0), 0)
            self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
            if bot_line:
                bot_line = Line(self, 420)
                # bot_line = lv.obj(self)
                # bot_line.set_size(420,1)
                # bot_line.add_style(
                #     StyleWrapper()
                #     .bg_color(lv_theme.CONT_ITEM_BLINE)
                #     , 0
                # )
                bot_line.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        def get_text(self) -> str:
            return self.content
