from .. import (
    font_GeistRegular30,
    font_GeistSemiBold30,
    font_GeistSemiBold48,
    lv,
    lv_theme,
)
from ..widgets.style import StyleWrapper


class ScreenTitle(lv.label):
    def __init__(
        self, parent, align_base, relative_pos: tuple, text: str, pos_y: int = 56
    ) -> None:
        super().__init__(parent)
        self.set_long_mode(lv.label.LONG.DOT)
        self.set_text(text)
        self.set_size(450, 38)
        if align_base:
            self.align_to(
                align_base, lv.ALIGN.OUT_BOTTOM_MID, relative_pos[0], relative_pos[1]
            )
        else:
            self.align(lv.ALIGN.TOP_LEFT, 12, pos_y)
        self.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold30)
            .text_color(lv_theme.DT_TITLE_FG)
            .text_align_center()
            .pad_all(0)
            .text_letter_space(-1),
            0,
        )


class Title(lv.label):
    def __init__(
        self,
        parent,
        align_base,
        text: str,
        # pos_y: int = 56,
        relative_pos: tuple = (15, 0),
        icon_path: str | None = None,
        relative_type=lv.ALIGN.OUT_BOTTOM_MID,
    ) -> None:
        super().__init__(parent)
        self.remove_style_all()
        self.add_style(StyleWrapper().pad_all(0), 0)
        self.set_text("")
        obj_height = lv.SIZE.CONTENT
        self.set_size(450, obj_height)
        if icon_path:
            self.icon = lv.img(self)
            self.icon.set_src(icon_path)
            # for i in range(100000):
            #     lv.timer_handler()
            #     w = self.icon.get_width()
            #     if w > 0:
            #         print(f"image loaded - i:{i} w:{w}")
            #         break
            # w = self.icon.get_width()

            # target_size = 100
            # if w > 0:
            #     zoom = int(128 * target_size / w)
            #     zoom = max(16, min(512, zoom))
            #     self.icon.set_zoom(zoom)
            self.icon.align(lv.ALIGN.LEFT_MID, 0, 0)
            self.text = lv.label(self)
            self.text.set_text(text)
            self.text.set_long_mode(lv.label.LONG.WRAP)
            self.text.set_size(360, obj_height)
            self.text.align_to(self.icon, lv.ALIGN.OUT_RIGHT_MID, 10, 0)
        else:
            self.text = lv.label(self)
            self.text.set_text(text)
            self.text.set_long_mode(lv.label.LONG.WRAP)
            self.text.set_size(450, obj_height)
            self.text.align(lv.ALIGN.TOP_MID, 0, 0)

        self.text.add_style(
            StyleWrapper()
            .text_font(font_GeistSemiBold48)
            .text_color(lv_theme.DT_TITLE_FG)
            .text_align_left()
            .pad_all(0)
            # .bg_color(lv_theme.TEST_FG)
            # .bg_opa(lv.OPA.COVER)
            # .pad_left(0)
            ,
            0,
        )
        if align_base:
            self.align_to(align_base, relative_type, relative_pos[0], relative_pos[1])
            self.text.add_style(
                StyleWrapper().text_align_center().pad_all(0),
                0,
            )
        else:
            self.align(lv.ALIGN.TOP_LEFT, relative_pos[0], relative_pos[1])


class SubTitle(lv.label):
    def __init__(self, parent, align_base, relative_pos: tuple, text: str) -> None:
        super().__init__(parent)
        self.set_long_mode(lv.label.LONG.WRAP)
        self.set_size(450, lv.SIZE.CONTENT)  # 456
        self.set_text(text)
        if align_base:
            self.align_to(
                align_base, lv.ALIGN.OUT_BOTTOM_MID, relative_pos[0], relative_pos[1]
            )
            self.add_style(
                StyleWrapper().text_align_center(),
                0,
            )
        else:
            self.align(lv.ALIGN.TOP_LEFT, relative_pos[0], relative_pos[1])

        self.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular30)
            .text_line_space(4)
            .text_color(lv_theme.DT_SUBTITLE_FG)
            .pad_ver(0)
            .text_letter_space(-1),
            0,
        )
