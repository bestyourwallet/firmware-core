from .. import (
    font_GeistMono28,
    font_GeistRegular20,
    font_GeistRegular26,
    font_GeistRegular30,
    font_GeistSemiBold26,
    font_GeistSemiBold30,
    lv,
    lv_theme,
    theme_path_default,
    theme_path_png,
)
from ..widgets.style import StyleWrapper
from .button import NormalButton
from .container import ContainerFlexCol
from .line import Line


class ListItemPictureWithCheckbox(lv.obj):
    def __init__(self, parent, text, img_path):
        super().__init__(parent)
        self.set_size(142, 400)
        # self.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        # self.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        self.img = lv.img(self)
        self.img.set_src(img_path)
        self.img.set_size(140, 233)
        self.img.align(lv.ALIGN.TOP_MID, 0, 0)
        self.img.add_style(StyleWrapper().pad_all(0), 0)
        self.add_style(
            StyleWrapper().pad_all(0).border_width(0).bg_opa(lv.OPA.TRANSP), 0
        )

        self.label = lv.label(self)
        self.label.set_long_mode(lv.label.LONG.WRAP)
        self.label.set_text(text)
        self.label.align_to(self.img, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
        self.label.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_color(lv_theme.CONT_ITEM_FG),
            0,
        )
        self.label.set_width(lv.SIZE.CONTENT)

        self.checkbox = lv.checkbox(self)
        self.checkbox.set_size(36, 36)
        self.checkbox.align_to(self.img, lv.ALIGN.OUT_BOTTOM_MID, 5, 77)
        self.checkbox.set_text("")
        self.checkbox.add_style(
            StyleWrapper()
            .radius(15)
            .pad_all(0)
            .bg_opa(lv.OPA.TRANSP)
            .border_opa(lv.OPA.TRANSP)
            .text_align(lv.TEXT_ALIGN.LEFT)
            .text_color(lv_theme.CONT_ITEM_CB_FG)
            .text_line_space(4),
            0,
        )
        self.checkbox.add_style(
            StyleWrapper()
            .radius(15)
            .pad_all(3)
            .bg_color(lv_theme.CONT_ITEM_CB_BG)
            .border_color(lv_theme.CONT_ITEM_CB_FG)
            .border_width(2)
            .border_opa(),
            lv.PART.INDICATOR | lv.STATE.DEFAULT,
        )
        self.checkbox.add_style(
            StyleWrapper()
            .radius(15)
            .pad_all(3)
            .bg_color(lv_theme.CONT_ITEM_CB_PBG)
            .text_color(lv_theme.CONT_ITEM_CB_PFG)
            .text_font(font_GeistMono28)
            .text_align(lv.TEXT_ALIGN.CENTER)
            .border_width(0)
            .bg_opa(),
            lv.PART.INDICATOR | lv.STATE.CHECKED,
        )
        self.checkbox.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.add_flag(lv.obj.FLAG.CLICKABLE)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

        self.checkbox.add_event_cb(self.checkbox_eventhandler, lv.EVENT.CLICKED, None)

    def get_checkbox(self):
        return self.checkbox

    def eventhandler(self, event):
        code = event.code
        # target = (
        #     event.get_target()
        # )  # noqa: F841  # TODO: keep for future event-target-specific behavior
        if code == lv.EVENT.CLICKED:
            self.checkbox.add_state(lv.STATE.CHECKED)
            lv.event_send(self.checkbox, lv.EVENT.VALUE_CHANGED, None)

    def checkbox_eventhandler(self, event):
        code = event.code
        if code == lv.EVENT.CLICKED:
            current_state = self.checkbox.get_state() & lv.STATE.CHECKED
            if current_state:
                self.checkbox.clear_state(lv.STATE.CHECKED)
            else:
                self.checkbox.add_state(lv.STATE.CHECKED)
            lv.event_send(self.checkbox, lv.EVENT.VALUE_CHANGED, None)


class ListItemWithLeadingCheckbox(lv.obj):
    def __init__(self, parent, text, radius: int = 12):
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper().bg_color(lv_theme.CONT_ITEM_DBG).bg_opa(lv.OPA.COVER)
            # .min_height(94)
            .radius(radius)
            .border_width(0)
            .pad_hor(15)
            .pad_ver(20)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_font(font_GeistRegular30)
            .text_letter_space(-2),
            0,
        )
        self.checkbox = lv.checkbox(self)
        self.checkbox.set_size(30, 30)
        self.checkbox.set_align(lv.ALIGN.LEFT_MID)
        self.checkbox.set_text("")
        self.checkbox.add_style(
            StyleWrapper()
            .pad_all(0)
            .bg_opa(lv.OPA.TRANSP)
            .border_opa(lv.OPA.TRANSP)
            .text_align(lv.TEXT_ALIGN.LEFT)
            .text_color(lv_theme.CONT_ITEM_CB_FG)
            .text_line_space(4),
            0,
        )
        self.checkbox.add_style(
            StyleWrapper()
            .radius(8)
            .pad_all(0)
            .bg_color(lv_theme.CONT_ITEM_CB_BG)
            .border_color(lv_theme.CONT_ITEM_CB_FG)
            .border_width(2)
            .border_opa(),
            lv.PART.INDICATOR | lv.STATE.DEFAULT,
        )
        self.checkbox.add_style(
            StyleWrapper()
            .radius(8)
            .bg_color(lv_theme.CONT_ITEM_CB_PBG)
            .text_color(lv_theme.CONT_ITEM_CB_PFG)
            .text_font(font_GeistMono28)
            .text_align(lv.TEXT_ALIGN.CENTER)
            .border_width(0)
            .bg_opa(),
            lv.PART.INDICATOR | lv.STATE.CHECKED,
        )
        self.checkbox.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.label = lv.label(self)
        self.label.remove_style_all()
        self.label.set_long_mode(lv.label.LONG.WRAP)
        self.label.set_size(380, lv.SIZE.CONTENT)
        self.label.align_to(self.checkbox, lv.ALIGN.OUT_RIGHT_TOP, 15, -4)
        self.label.set_text(text)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE | lv.obj.FLAG.CLICKABLE)
        self.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

    def eventhandler(self, event):
        code = event.code
        target = event.get_target()
        # if target == self.checkbox ignore instead. because value_change event is also triggered which needless to deal with
        if code == lv.EVENT.CLICKED and target != self.checkbox:
            if self.checkbox.get_state() & lv.STATE.CHECKED:
                self.checkbox.clear_state(lv.STATE.CHECKED)
            else:
                self.checkbox.add_state(lv.STATE.CHECKED)
            lv.event_send(self.checkbox, lv.EVENT.VALUE_CHANGED, None)

    def get_checkbox(self):
        return self.checkbox

    def get_label(self):
        return self.label

    def enable_bg_color(self, enable: bool = True):
        if enable:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.CONT_ITEM_BG),
                0,
            )
        else:
            self.add_style(
                StyleWrapper().bg_color(lv_theme.CONT_ITEM_DBG),
                0,
            )


class DisplayItem(lv.obj):
    def __init__(
        self,
        parent,
        title,
        content,
        bg_color=None,
        radius: int = 0,
        font=font_GeistRegular26,
        padding_hor: int = 15,
        label_hor: int = 0,
        padding_ver: int = 20,
        bot_line: bool = False,
        font_space=-1,
        title_index: int = 0,
    ):
        super().__init__(parent)
        self.remove_style_all()
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper()
            .bg_color(bg_color)
            .bg_opa(lv.OPA.COVER)
            .min_height(100 if content else 60)
            .border_width(0)
            .pad_hor(padding_hor)
            .pad_ver(padding_ver)
            .radius(radius)
            .text_font(font)
            .text_align_left(),
            0,
        )
        if title:
            if title_index > 0:
                self.title_index = lv.img(self)
                self.title_index.set_src(
                    theme_path_png(f"group-circle-num-{title_index}")
                )
                self.title_index.align(lv.ALIGN.TOP_LEFT, 0, 0)
            self.label_top = lv.label(self)
            self.label_top.set_recolor(True)
            self.label_top.set_size(420, lv.SIZE.CONTENT)
            self.label_top.set_long_mode(lv.label.LONG.WRAP)
            self.label_top.set_text(title)
            self.label_top.align(lv.ALIGN.TOP_LEFT, 0, 0)
            self.label_top.add_style(
                StyleWrapper()
                .text_color(lv_theme.CONT_ITEM_TITLE_FG)
                .text_font(font_GeistSemiBold26)
                .pad_all(0)
                .text_letter_space(font_space),
                0,
            )
            if title_index > 0:
                self.label_top.set_size(380, lv.SIZE.CONTENT)
                self.label_top.align_to(
                    self.title_index, lv.ALIGN.OUT_RIGHT_TOP, 10, -5
                )
            else:
                self.label_top.set_size(420, lv.SIZE.CONTENT)
                self.label_top.align(lv.ALIGN.TOP_LEFT, 0, 0)

        self.label = lv.label(self)
        # self.label.set_size(lv.pct(100), lv.SIZE.CONTENT)
        self.label.set_recolor(True)
        self.label.set_text(content)
        self.label.set_size(420, lv.SIZE.CONTENT)
        self.label.add_style(
            StyleWrapper()
            .pad_all(0)
            .text_color(lv_theme.CONT_ITEM_SUB_FG if title else lv_theme.CONT_ITEM_FG)
            .text_line_space(6)
            .text_letter_space(font_space),
            0,
        )

        if title:
            self.label.align_to(self.label_top, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
            self.label.set_x(label_hor)
        else:
            self.label.align(lv.ALIGN.TOP_LEFT, label_hor, 0)
        if bot_line:
            self.line = lv.line(self)
            self.line.set_size(420, 1)
            self.line.add_style(
                StyleWrapper().bg_color(lv_theme.CONT_ITEM_BLINE).bg_opa(), 0
            )
            self.line.align_to(self.label, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 15)


class DisplayItemWithFont_30(DisplayItem):
    def __init__(
        self,
        parent,
        title,
        content,
        bg_color=None,
        radius: int = 0,
        font=font_GeistRegular30,
        url: str | None = None,
    ) -> None:
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        super().__init__(parent, title, content, bg_color, radius, font)
        self.label_top.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold30)
            .text_color(lv_theme.CONT_ITEM_SUB_FG),
            0,
        )
        self.label.add_style(
            StyleWrapper().text_color(lv_theme.CONT_ITEM_TITLE_FG),
            0,
        )
        if url:
            self.url = lv.label(self)
            self.url.set_size(420, lv.SIZE.CONTENT)
            self.url.set_text(url)
            self.url.add_style(
                StyleWrapper()
                .text_color(lv_theme.CONT_ITEM_LINK_FG)
                .text_font(font_GeistRegular20)
                .text_line_space(6)
                .text_letter_space(-1),
                0,
            )
            self.url.align_to(self.label, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 4)


class CardHeader(lv.obj):
    def __init__(self, parent, title, icon):
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(450, 50)
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa()
            .border_width(0)
            .pad_ver(16)
            .pad_bottom(0)
            .pad_hor(24)
            .radius(0)
            .text_font(font_GeistSemiBold26)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_align_left(),
            0,
        )
        self.icon = lv.img(self)
        self.icon.set_src(icon)
        # self.icon.set_size(29, 29)
        self.icon.align(lv.ALIGN.TOP_LEFT, -6, -4)
        self.label = lv.label(self)
        self.label.set_text(title)
        self.label.set_size(360, lv.SIZE.CONTENT)
        self.label.set_long_mode(lv.label.LONG.WRAP)
        self.label.align_to(self.icon, lv.ALIGN.OUT_RIGHT_MID, 12, 0)
        self.label.add_style(StyleWrapper().text_color(lv_theme.CONT_ITEM_TITLE_FG), 0)
        # self.line = lv.line(self)
        # self.line.set_size(408, 1)
        # self.line.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.CONT_ITEM_BLINE)
        #     .bg_opa()
        #     , 0
        # )
        # self.line.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 14)
        self.line = Line(self, 420)  # , line_color=lv_theme.TEST_FG)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)

        # self.line = lv.obj(self)
        # self.line.set_size(420,1)
        # self.line.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.CONT_ITEM_BLINE)
        #     .border_opa(lv.OPA.TRANSP)
        #     .border_width(0)
        #     , 0
        # )
        self.line.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 8)


class CardItem(CardHeader):
    def __init__(self, parent, title, content, icon):
        super().__init__(parent, title, icon)
        self.add_style(StyleWrapper().radius(10).pad_bottom(24), 0)
        self.set_size(450, lv.SIZE.CONTENT)
        self.content = lv.obj(self)
        self.content.set_size(408, lv.SIZE.CONTENT)
        self.content.add_style(
            StyleWrapper()
            .pad_all(12)
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa()
            .radius(10)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_font(font_GeistMono28)
            .border_width(0)
            .max_height(364)
            .text_align_left(),
            0,
        )
        self.content_label = lv.label(self.content)
        self.content_label.set_size(384, lv.SIZE.CONTENT)
        self.content_label.set_long_mode(lv.label.LONG.WRAP)
        self.content_label.set_text(content)
        self.content_label.add_style(
            StyleWrapper().text_letter_space(-2).max_height(320), 0
        )
        self.content_label.set_align(lv.ALIGN.CENTER)
        self.content.align_to(self.line, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)


class DisplayItemNoBgc(DisplayItem):
    def __init__(self, parent, title, content):
        super().__init__(parent, title, content, bg_color=lv_theme.CONT_ITEM_BG)
        self.add_style(
            StyleWrapper().min_height(0).pad_hor(0),
            0,
        )


class ImgGridItem(lv.obj):
    """Home Screen setting display"""

    def __init__(
        self,
        parent,
        col_num,
        row_num,
        file_name: str,
        path_dir: str,
        img_path_other: str | None = None,
        is_internal: bool = False,
    ):
        if img_path_other is None:
            img_path_other = theme_path_png("checked-solid")
        super().__init__(parent)
        self.set_grid_cell(
            lv.GRID_ALIGN.CENTER, col_num, 1, lv.GRID_ALIGN.CENTER, row_num, 1
        )
        self.is_internal = is_internal
        self.file_name = file_name
        self.zoom_path = f"{path_dir}_{file_name}"
        self.set_size(146, 246)

        self.img = lv.img(self)
        self.img.set_src(self.zoom_path)
        self.img.align(lv.ALIGN.TOP_LEFT, -10, -2)
        self.img.set_size(146, 246)  # 217  140 233
        self.add_style(StyleWrapper().border_width(0).bg_opa(lv.OPA.TRANSP), 0)
        self.img_path = self.zoom_path.replace("zoom-", "")
        # print('zoom: ', self.img_path)
        self.check = lv.img(self)
        self.check.set_src(img_path_other)
        self.check.center()
        self.set_checked(False)
        self.add_flag(lv.obj.FLAG.CLICKABLE)
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        # self.text = lv.label(self)
        # tn = self.file_name.replace("zoom-", "")
        # self.text.set_text(tn.rsplit('.',1)[0].rsplit('-',1)[0])
        # self.text.align_to(self.img, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)
        # self.text.add_style(
        #     StyleWrapper()
        #     .border_width(0)
        #     .bg_color(lv_colors.UKEY_RED_1)
        #     .bg_opa(lv.OPA.COVER),
        #     0
        # )
        # print(tn.rsplit('.',1)[0].rsplit('-',1)[0])
        # self.text.set_style_bg_color(lv_colors.UKEY_GREEN_1, 0)
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)  # text.

    def set_checked(self, checked: bool):
        if checked:
            self.check.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.check.add_flag(lv.obj.FLAG.HIDDEN)


class DisplayItemWithTextPairs(lv.obj):
    def __init__(
        self,
        parent,
        title,
        content_pairs,
        bg_color=None,
        radius=0,
        font=font_GeistRegular26,
    ):
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper()
            .bg_color(bg_color)
            .bg_opa(lv.OPA.COVER)
            .min_height(82)
            .border_width(0)
            .pad_hor(15)
            .pad_ver(12)
            .radius(radius)
            .text_font(font)
            .text_align_left(),
            0,
        )
        base_obj = None
        if title:
            self.label_top = lv.label(self)
            self.label_top.set_recolor(True)
            self.label_top.set_size(lv.pct(100), lv.SIZE.CONTENT)
            self.label_top.set_long_mode(lv.label.LONG.WRAP)
            self.label_top.set_text(title)
            self.label_top.set_align(lv.ALIGN.TOP_LEFT)
            self.label_top.add_style(
                StyleWrapper()
                .text_color(lv_theme.CONT_ITEM_SUB_FG)
                .text_letter_space(-1),
                0,
            )
            base_obj = self.label_top

        # y_offset = self.label_top.get_height() + 40
        for left_text, right_text in content_pairs:
            cont_tmp = lv.obj(self)
            cont_tmp.set_size(lv.pct(100), lv.SIZE.CONTENT)
            cont_tmp.align_to(base_obj, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
            cont_tmp.add_style(
                StyleWrapper()
                .bg_opa(lv.OPA.TRANSP)
                .border_opa(lv.OPA.TRANSP)
                .pad_all(0),
                0,
            )
            base_obj = cont_tmp
            label_left = lv.label(cont_tmp)
            label_left.set_text(left_text)
            label_left.align(lv.ALIGN.TOP_LEFT, 0, 0)
            label_right = lv.label(cont_tmp)
            label_right.set_text(right_text)
            label_right.align_to(label_left, lv.ALIGN.OUT_RIGHT_MID, 0, 0)
            label_right.set_long_mode(lv.label.LONG.WRAP)
            label_right.set_width(360)
            label_left.add_style(
                StyleWrapper()
                .text_color(
                    lv_theme.CONT_ITEM_TITLE_FG if title else lv_theme.CONT_ITEM_FG
                )
                .text_letter_space(-1),
                0,
            )
            label_right.add_style(
                StyleWrapper()
                .text_color(
                    lv_theme.CONT_ITEM_TITLE_FG if title else lv_theme.CONT_ITEM_FG
                )
                .text_letter_space(-1),
                0,
            )
            # h_left = label_left.get_height()
            # h_right = label_right.get_height()
            # print('get_height left:', h_left, 'right:', h_right)
            # y_offset += max(h_left, h_right) + 40


class DisplayItemWithFont_TextPairs(DisplayItemWithTextPairs):
    def __init__(
        self,
        parent,
        title,
        content_pairs,
        bg_color=None,
        radius: int = 0,
        font=font_GeistRegular30,
    ):
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        super().__init__(parent, title, content_pairs, bg_color, radius, font)


class ShortInfoItem(lv.obj):
    def __init__(
        self,
        parent,
        img_src,
        title_text,
        subtitle_text,
        bg_color=None,
        border_color=None,
        title_color=None,
        subtitle_color=None,
        icon_boarder_color=None,
    ):
        super().__init__(parent)
        self.remove_style_all()
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        if border_color is None:
            border_color = lv_theme.CONT_ITEM_BOARD_BG
        if title_color is None:
            title_color = lv_theme.DT_TITLE_FG
        if subtitle_color is None:
            subtitle_color = lv_theme.DT_TIP_FG
        if icon_boarder_color is None:
            icon_boarder_color = lv_theme.CONT_ITEM_SUB_BG

        self.set_size(400, 70)
        self.add_style(
            StyleWrapper()
            .bg_color(bg_color)
            .bg_opa(lv.OPA._10)
            .radius(40)
            .border_width(1)
            .border_color(border_color)
            .border_opa(lv.OPA._10),
            0,
        )
        self.clear_flag(lv.obj.FLAG.SCROLLABLE)

        if img_src and img_src != theme_path_default("evm-none.png"):
            self.bottom_circle = lv.obj(self)
            self.bottom_circle.set_size(70, 70)
            self.bottom_circle.align(lv.ALIGN.LEFT_MID, -1, 0)
            self.bottom_circle.add_style(
                StyleWrapper()
                .bg_color(icon_boarder_color)
                .bg_opa(lv.OPA._50)
                .radius(35)
                .border_width(0),
                0,
            )
            self.bottom_circle.clear_flag(lv.obj.FLAG.SCROLLABLE)

            self.middle_circle = lv.obj(self)
            self.middle_circle.set_size(60, 60)
            self.middle_circle.align_to(self.bottom_circle, lv.ALIGN.CENTER, 0, 0)
            self.middle_circle.add_style(
                StyleWrapper()
                .bg_color(lv_theme.CONT_ITEM_SUB_BG)
                .bg_opa(lv.OPA.COVER)
                .radius(30)
                .border_width(0),
                0,
            )
            self.middle_circle.clear_flag(lv.obj.FLAG.SCROLLABLE)

            self.img = lv.img(self)
            self.img.set_src(img_src)
            self.img.set_zoom(133)
            self.img.align_to(self.middle_circle, lv.ALIGN.CENTER, 0, 0)
            self.img.set_style_radius(25, 0)
            self.img.move_foreground()
        else:
            self.img = lv.img(self)
            self.img.set_src(theme_path_default("tools_turbo-send.png"))
            self.img.set_style_radius(35, 0)
            self.img.move_foreground()
            self.img.align(lv.ALIGN.LEFT_MID, -1, 0)

        self.title = lv.label(self)
        self.title.set_text(title_text)
        self.title.set_long_mode(lv.label.LONG.DOT)
        self.title.set_width(320)
        self.title.add_style(
            StyleWrapper()
            .text_color(title_color)
            .text_font(font_GeistSemiBold26)
            .text_letter_space(0),
            0,
        )
        if hasattr(self, "bottom_circle"):
            self.title.align_to(self.bottom_circle, lv.ALIGN.OUT_RIGHT_MID, 14, -12)
        else:
            self.title.align_to(self.img, lv.ALIGN.OUT_RIGHT_MID, 14, -12)

        self.subtitle = lv.label(self)
        self.subtitle.set_text(subtitle_text)
        self.subtitle.set_long_mode(lv.label.LONG.DOT)
        self.subtitle.set_width(320)
        self.subtitle.add_style(
            StyleWrapper()
            .text_color(subtitle_color)
            .text_font(font_GeistRegular20)
            .text_letter_space(0),
            0,
        )
        self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 4)

        self.add_flag(lv.obj.FLAG.CLICKABLE)


class RawDataOverviewWithTitle(lv.obj):
    def __init__(
        self,
        parent,
        title,
        content,
        brief_tip: str | None = None,
        primary_color=None,
        bg_color=None,
        radius: int = 0,
        font=font_GeistRegular26,
    ):
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        if primary_color is None:
            primary_color = lv_theme.APP_CORRECT_BG
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper()
            .bg_color(bg_color)
            .bg_opa(lv.OPA.COVER)
            .min_height(82)
            .border_width(0)
            .pad_hor(24)
            .pad_ver(12)
            .radius(radius)
            .text_font(font)
            .text_align_left(),
            0,
        )
        if title:
            self.title = lv.label(self)
            self.title.set_recolor(True)
            self.title.set_size(lv.pct(100), lv.SIZE.CONTENT)
            self.title.set_long_mode(lv.label.LONG.WRAP)
            self.title.set_text(title)
            self.title.set_align(lv.ALIGN.TOP_LEFT)
            self.title.add_style(
                StyleWrapper()
                .text_color(lv_theme.CONT_ITEM_TITLE_FG)
                .text_letter_space(-1),
                0,
            )
        self.content = self.RawDataOverview(self, content, brief_tip, primary_color)
        self.content.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 4)

    class RawDataOverview(lv.obj):
        def __init__(
            self,
            parent,
            content,
            brief_tip: str | None = None,
            primary_color=lv_theme.APP_CORRECT_BG,
        ):
            super().__init__(parent)
            self.remove_style_all()
            self.set_size(408, lv.SIZE.CONTENT)
            self.add_style(
                StyleWrapper()
                .pad_all(12)
                .bg_color(lv_theme.CONT_ITEM_SUB_BG)
                .bg_opa()
                .radius(24)
                .text_color(lv_theme.CONT_ITEM_SUB_FG)
                .text_font(font_GeistMono28)
                .border_width(0)
                .max_height(364)
                .text_align_left(),
                0,
            )
            self.long_message = False
            self.full_message = content
            self.primary_color = primary_color
            if len(content) > 150:
                self.message = content[:147] + "..."
                self.long_message = True
            else:
                self.message = content
            self.content_label = lv.label(self)
            self.content_label.set_size(384, lv.SIZE.CONTENT)
            self.content_label.set_long_mode(lv.label.LONG.WRAP)
            self.content_label.set_text(self.message)
            self.content_label.add_style(
                StyleWrapper().text_letter_space(-2).max_height(320), 0
            )
            self.content_label.set_align(lv.ALIGN.CENTER)
            if self.long_message:
                self.show_full_message = NormalButton(self.content_label, brief_tip)
                self.show_full_message.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_message.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_message.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_message.remove_style(
                    None, lv.PART.MAIN | lv.STATE.PRESSED
                )
                self.show_full_message.add_event_cb(
                    self.on_click, lv.EVENT.CLICKED, None
                )

        def on_click(self, event_obj):
            code = event_obj.code
            target = event_obj.get_target()
            if code == lv.EVENT.CLICKED:
                from trezor.lvglui.scrs.components.pageable import PageAbleMessage
                from trezor.lvglui.i18n import gettext as _
                from trezor.lvglui.i18n import keys as i18n_keys

                if target == self.show_full_message:
                    PageAbleMessage(
                        _(i18n_keys.TITLE__MESSAGE),
                        self.full_message,
                        None,
                        primary_color=self.primary_color,
                        font=font_GeistMono28,
                        confirm_text=None,
                        cancel_text=None,
                    )


class DisplayItemWithFlexColPanel(lv.obj):
    def __init__(
        self,
        parent,
        title,
        bg_color=None,
        radius: int = 0,
        font=font_GeistRegular26,
    ):
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(450, lv.SIZE.CONTENT)
        self.add_style(
            StyleWrapper()
            .bg_color(bg_color)
            .bg_opa(lv.OPA.COVER)
            .min_height(82)
            .border_width(0)
            .pad_hor(24)
            .pad_ver(12)
            .radius(radius)
            .text_font(font)
            .text_align_left(),
            0,
        )
        self.title = lv.label(self)
        self.title.set_recolor(True)
        self.title.set_size(lv.pct(100), lv.SIZE.CONTENT)
        self.title.set_long_mode(lv.label.LONG.WRAP)
        self.title.set_text(title)
        self.title.align(lv.ALIGN.TOP_LEFT, 0, 0)
        self.title.add_style(
            StyleWrapper()
            .text_color(lv_theme.CONT_ITEM_TITLE_FG)
            .text_letter_space(-1),
            0,
        )
        self.flex_col_panel = ContainerFlexCol(self, None, padding_row=0, no_align=True)
        self.flex_col_panel.set_size(408, lv.SIZE.CONTENT)
        self.flex_col_panel.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_SUB_BG)
            .bg_opa(lv.OPA.COVER)
            .radius(24),
            0,
        )
        self.flex_col_panel.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 4)
