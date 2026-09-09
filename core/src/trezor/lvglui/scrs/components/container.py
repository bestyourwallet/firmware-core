import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]

from .. import font_GeistRegular26, lv_theme
from ..widgets.style import StyleWrapper


class ContainerFlexCol(lv.obj):
    def __init__(
        self,
        parent,
        align_base,
        align=lv.ALIGN.OUT_BOTTOM_MID,
        bg_opa=lv.OPA.TRANSP,
        pos: tuple = (0, 40),
        padding_row: int = 8,
        clip_corner: bool = True,
        no_align: bool = False,
        radius: int = 20,
        height=None,
        # description=None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.remove_style_all()
        if height is not None:
            self.set_size(450, height)
        else:
            self.set_size(450, lv.SIZE.CONTENT)  # lv.pct(100)
        if not no_align:
            if align_base is None:
                self.align(lv.ALIGN.BOTTOM_MID, 0, -8)
            else:
                self.align_to(align_base, align, 0, pos[1])
        self.add_style(
            StyleWrapper()
            .bg_opa(bg_opa)
            .radius(radius)  # 40
            .bg_color(lv_theme.CONT_BG)
            # .bg_opa(lv.OPA.TRANSP)
            .border_width(0)
            .pad_all(0)
            .clip_corner(True if clip_corner else False)
            .pad_row(padding_row),
            0,
        )
        self.clear_flag(lv.obj.FLAG.CLICKABLE)
        self.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.set_flex_align(
            lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        # self.set_description(description)

    def add_dummy(self, bg_color=None):
        if bg_color is None:
            bg_color = lv_theme.CONT_ITEM_BG
        dummy = lv.obj(self)
        dummy.remove_style_all()
        dummy.set_size(lv.pct(100), 12)
        dummy.add_style(StyleWrapper().bg_color(bg_color).bg_opa(), 0)

    def refresh_theme(self):
        self.set_style_bg_color(lv_theme.CONT_BG, 0)
        self.description.set_style_text_color(lv_theme.DT_DESC_FG, 0)

    def set_description(self, text: str | None = None):
        if __debug__:
            print(f"ContainerFlexCol set description {text}")
        if text is None or len(text.strip()) == 0:
            if hasattr(self, "description") and not self.description.has_flag(
                lv.obj.FLAG.HIDDEN
            ):
                self.description.add_flag(lv.obj.FLAG.HIDDEN)
            return

        if not hasattr(self, "description"):
            self.description = lv.label(self.parent)
            self.description.set_size(450, lv.SIZE.CONTENT)
            self.description.set_long_mode(lv.label.LONG.WRAP)
            self.description.add_style(
                StyleWrapper()
                .text_color(lv_theme.DT_DESC_FG)  # DT_TIP_FG
                .text_font(font_GeistRegular26)
                .text_line_space(3),
                0,
            )
        if self.description.has_flag(lv.obj.FLAG.HIDDEN):
            self.description.clear_flag(lv.obj.FLAG.HIDDEN)

        self.description.set_text(text)
        self.description.align_to(self, lv.ALIGN.OUT_BOTTOM_LEFT, 8, 16)


class ContainerFlexRow(lv.obj):
    def __init__(
        self,
        parent,
        align_base,
        align=lv.ALIGN.OUT_TOP_MID,
        pos: tuple = (0, -0),
        padding_col: int = 8,
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
        if align_base:
            self.align_to(align_base, align, pos[0], pos[1])
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_BG)
            .bg_opa(lv.OPA.TRANSP)
            .radius(0)
            .border_width(0)
            .pad_column(padding_col),
            0,
        )
        self.set_flex_flow(lv.FLEX_FLOW.ROW)
        # align style of the items in the container
        self.set_flex_align(
            lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )


class ContainerFlex(lv.obj):
    def __init__(
        self,
        parent,
        align_base,
        align=lv.ALIGN.OUT_TOP_MID,
        pos: tuple = (0, -48),
        padding_col: int = 8,
        flex_flow: lv.FLEX_FLOW = lv.FLEX_FLOW.ROW,
        main_align: lv.FLEX_ALIGN = lv.FLEX_ALIGN.CENTER,
        cross_align: lv.FLEX_ALIGN = lv.FLEX_ALIGN.CENTER,
        track_align: lv.FLEX_ALIGN = lv.FLEX_ALIGN.CENTER,
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.set_size(lv.pct(100), lv.SIZE.CONTENT)
        if align_base:
            self.align_to(align_base, align, pos[0], pos[1])
        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_BG)
            .bg_opa(lv.OPA.TRANSP)
            .radius(0)
            .border_width(0)
            .pad_column(padding_col),
            0,
        )
        self.set_flex_flow(flex_flow)
        # align style of the items in the container
        self.set_flex_align(main_align, cross_align, track_align)
        self.set_layout(lv.LAYOUT_FLEX.value)


class ContainerGrid(lv.obj):
    def __init__(
        self,
        parent,
        row_dsc,
        col_dsc,
        align_base=None,
        align_type=lv.ALIGN.OUT_BOTTOM_LEFT,
        pos: tuple = (0, 40),
        pad_gap=16,
    ) -> None:
        super().__init__(parent)
        self.set_size(450, lv.SIZE.CONTENT)
        # print('align_base: ', align_base, pos)
        if align_base:
            self.align_to(align_base, lv.ALIGN.OUT_BOTTOM_MID, pos[0], pos[1])
        else:
            self.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        self.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_BG)
            .bg_opa(lv.OPA.TRANSP)
            .radius(0)
            .pad_gap(pad_gap)
            .pad_all(0)
            .border_width(0)
            .grid_column_dsc_array(col_dsc)
            .grid_row_dsc_array(row_dsc),
            0,
        )
        self.set_grid_align(lv.GRID_ALIGN.SPACE_AROUND, lv.GRID_ALIGN.END)
        self.set_layout(lv.LAYOUT_GRID.value)
