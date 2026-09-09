from typing import TYPE_CHECKING

import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]

if TYPE_CHECKING:
    from enum import IntEnum
else:
    IntEnum = object


class BannerType(IntEnum):
    Default = 0
    HighLight = 1
    Warning = 2
    Danger = 3
    DefaultLight = 4


class Banner(lv.obj):
    def __init__(self, parent, level: BannerType, text: str, title: str = None) -> None:
        from trezor.lvglui.lv_theme import lv_theme
        from trezor.lvglui.scrs import (
            font_GeistRegular26,
            font_GeistSemiBold26,
            theme_path_png,
        )
        from trezor.lvglui.scrs.widgets.style import StyleWrapper

        super().__init__(parent)
        self.remove_style_all()
        color, icon_path = lv_theme.BANNER_STYLE.get(
            level, lv_theme.BANNER_STYLE[BannerType.Default]
        )
        self.add_style(
            StyleWrapper()
            .width(450)
            .height(lv.SIZE.CONTENT)
            .text_font(font_GeistRegular26)
            .text_color(color)
            .border_color(color)
            .text_letter_space(-1)
            .bg_color(color)
            .bg_opa(5)
            .radius(12)
            .border_width(1)
            .pad_hor(15)
            .pad_ver(16),
            0,
        )
        self.align(lv.ALIGN.BOTTOM_MID, 0, -8)
        self.lead_icon = lv.img(self)
        self.lead_icon.set_src(theme_path_png(f"circle-alert-{icon_path}"))
        self.lead_icon.align(lv.ALIGN.LEFT_MID, 0, 0)
        if title:
            self.banner_title = lv.label(self)
            self.banner_title.set_size(368, lv.SIZE.CONTENT)
            self.banner_title.set_long_mode(lv.label.LONG.WRAP)
            self.banner_title.add_style(
                StyleWrapper().text_font(font_GeistSemiBold26),
                0,
            )
            self.banner_title.align_to(self.lead_icon, lv.ALIGN.OUT_RIGHT_TOP, 8, 3)
            self.banner_title.set_text(title)
        self.banner_desc = lv.label(self)
        self.banner_desc.set_size(368, lv.SIZE.CONTENT)
        self.banner_desc.set_long_mode(lv.label.LONG.WRAP)
        if title:
            self.banner_desc.align_to(self.banner_title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 8)
        else:
            self.banner_desc.align_to(self.lead_icon, lv.ALIGN.OUT_RIGHT_TOP, 8, 3)
        self.banner_desc.set_text(text)
