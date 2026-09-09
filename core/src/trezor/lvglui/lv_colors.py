import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]


def LV_COLOR_MAKE(r, g, b):
    #    return lv.color_hex(r<<16| g<<8 |b)
    return lv.color_make(r, g, b)


class lv_colors:
    WHITE = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF)
    SILVER = LV_COLOR_MAKE(0xC0, 0xC0, 0xC0)
    GRAY = LV_COLOR_MAKE(0x80, 0x80, 0x80)
    BLACK = LV_COLOR_MAKE(0x00, 0x00, 0x00)
    RED = LV_COLOR_MAKE(0xFF, 0x00, 0x00)
    MAROON = LV_COLOR_MAKE(0x80, 0x00, 0x00)
    YELLOW = LV_COLOR_MAKE(0xFF, 0xFF, 0x00)
    OLIVE = LV_COLOR_MAKE(0x80, 0x80, 0x00)
    LIME = LV_COLOR_MAKE(0x00, 0xFF, 0x00)
    GREEN = LV_COLOR_MAKE(0x00, 0x80, 0x00)
    CYAN = LV_COLOR_MAKE(0x00, 0xFF, 0xFF)
    AQUA = CYAN
    TEAL = LV_COLOR_MAKE(0x00, 0x80, 0x80)
    BLUE = LV_COLOR_MAKE(0x00, 0x00, 0xFF)
    NAVY = LV_COLOR_MAKE(0x00, 0x00, 0x80)
    MAGENTA = LV_COLOR_MAKE(0xFF, 0x00, 0xFF)
    PURPLE = LV_COLOR_MAKE(0x80, 0x00, 0x80)
    ORANGE = LV_COLOR_MAKE(0xFF, 0xA5, 0x00)

    UKEY_O_GREEN = LV_COLOR_MAKE(0x00, 0xFF, 0x33)  # ok button bg
    UKEY_O_GREEN_1 = LV_COLOR_MAKE(0x00, 0xB8, 0x12)
    UKEY_O_GREEN_2 = LV_COLOR_MAKE(0x00, 0xBE, 0x2D)
    UKEY_O_RED = LV_COLOR_MAKE(0x29, 0x07, 0x00)  #
    UKEY_O_RED_1 = LV_COLOR_MAKE(
        0xFF, 0x11, 0x00
    )  # danger button list item left/right text/number keyboard delete button
    UKEY_O_RED_2 = LV_COLOR_MAKE(0xDE, 0x12, 0x00)
    UKEY_O_RED_3 = LV_COLOR_MAKE(0xBE, 0x13, 0x00)
    UKEY_O_BLACK = LV_COLOR_MAKE(
        0x4B, 0x4B, 0x4B
    )  # cancel button bg enable/number keyboard
    UKEY_O_BLACK_1 = LV_COLOR_MAKE(0x33, 0x33, 0x33)  # cancel button bg disable
    UKEY_O_BLACK_2 = LV_COLOR_MAKE(0x1A, 0x1A, 0x1A)
    UKEY_O_BLACK_3 = LV_COLOR_MAKE(0x1E, 0x1E, 0x1E)
    UKEY_O_BLACK_4 = LV_COLOR_MAKE(0x0F, 0x0F, 0x0F)  # slider main disable color
    UKEY_O_BLACK_5 = LV_COLOR_MAKE(0x16, 0x16, 0x16)  # arrow btn disable color

    UKEY_O_GRAY = LV_COLOR_MAKE(
        0x96, 0x96, 0x96
    )  # cancel button disable text/ display item key switch enable border color
    UKEY_O_GRAY_3 = LV_COLOR_MAKE(0x2D, 0x2D, 0x2D)
    UKEY_O_GRAY_4 = LV_COLOR_MAKE(0xB4, 0xB4, 0xB4)
    LIGHT_GRAY = LV_COLOR_MAKE(
        0xD2, 0xD2, 0xD2
    )  # list item right gray text/ mnemonic tip words
    GRAY_1 = LV_COLOR_MAKE(0x61, 0x61, 0x63)  # switch main bg
    WHITE_1 = LV_COLOR_MAKE(0x99, 0x99, 0x99)  # checkbox text deselect
    WHITE_2 = LV_COLOR_MAKE(0x87, 0x87, 0x87)  # subtitle text
    WHITE_3 = LV_COLOR_MAKE(0xE5, 0xE5, 0xE5)  # scrollbar

    UKEY_O_WHITE_4 = LV_COLOR_MAKE(0xF0, 0xF0, 0xF0)  # slider enable text color
    GRAY_2 = LV_COLOR_MAKE(0xA6, 0xA6, 0xA6)  # page_able gray dot indicator
    UKEY_O_YELLOW = LV_COLOR_MAKE(0xFF, 0xD5, 0x00)
    UKEY_O_GRAY_1 = LV_COLOR_MAKE(0x69, 0x69, 0x69)  # slider border color disable
    UKEY_O_GRAY_2 = LV_COLOR_MAKE(0x3C, 0x3C, 0x3C)  # switch border color disable
    UKEY_O_PURPLE = LV_COLOR_MAKE(0x9F, 0x00, 0xFF)
    UKEY_O_DARK_BLUE = LV_COLOR_MAKE(0x00, 0x18, 0x47)
    UKEY_O_BLUE = LV_COLOR_MAKE(0x41, 0x78, 0xFF)
    UKEY_O_YELLOW_1 = LV_COLOR_MAKE(0xE0, 0xBC, 0x00)
    UKEY_O_YELLOW_2 = LV_COLOR_MAKE(0x33, 0x2C, 0x00)
    UKEY_O_YELLOW_3 = LV_COLOR_MAKE(0xC1, 0xA4, 0x00)
    UKEY_O_PURPLE_1 = LV_COLOR_MAKE(0x1A, 0x14, 0x31)

    UKEY_WHITE_1 = LV_COLOR_MAKE(0xF2, 0xF3, 0xF4)
    UKEY_WHITE_6 = LV_COLOR_MAKE(0xF0, 0xF1, 0xF2)
    UKEY_WHITE_3 = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF)
    UKEY_WHITE_2 = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF)
    UKEY_WHITE_4 = LV_COLOR_MAKE(0xDF, 0xE3, 0xE5)
    UKEY_WHITE_5 = LV_COLOR_MAKE(0xFA, 0xFA, 0xFA)
    UKEY_WHITE_7 = LV_COLOR_MAKE(0xE9, 0xE9, 0xE9)

    UKEY_WHITE_8 = LV_COLOR_MAKE(0xED, 0xEE, 0xF0)

    UKEY_BLACK_1 = LV_COLOR_MAKE(0x10, 0x10, 0x10)
    UKEY_BLACK_2 = LV_COLOR_MAKE(0x10, 0x10, 0x10)
    UKEY_BLACK_3 = LV_COLOR_MAKE(0x00, 0x00, 0x00)
    UKEY_BLACK_4 = LV_COLOR_MAKE(0x30, 0x30, 0x30)

    UKEY_GRAY_1 = LV_COLOR_MAKE(0x6A, 0x71, 0x81)
    UKEY_GRAY_2 = LV_COLOR_MAKE(0x9F, 0xA5, 0xB3)
    UKEY_GRAY_3 = LV_COLOR_MAKE(0x43, 0x47, 0x50)
    UKEY_BLUE_1 = LV_COLOR_MAKE(0x4A, 0x52, 0xFF)
    UKEY_GREEN_1 = LV_COLOR_MAKE(0x28, 0xB8, 0x70)
    UKEY_RED_1 = LV_COLOR_MAKE(0xF0, 0x43, 0x49)
    UKEY_RED_2 = LV_COLOR_MAKE(0xFC, 0xDF, 0xE0)
