import lvgl as lv  # type: ignore [Import "lvgl" could not be resolved]

from ..lv_colors import lv_colors


class theme_colors:
    class colors:
        BLACK_01 = lv.color_hex(0x000000)
        BLACK_02 = lv.color_hex(0x222222)
        BLACK_03 = lv.color_hex(0x303030)
        BLACK_04 = lv.color_hex(0x333333)

        GRAY_01 = lv.color_hex(0x9FA5B3)
        GRAY_02 = lv.color_hex(0x6A7181)
        GRAY_03 = lv.color_hex(0x666666)
        GRAY_04 = lv.color_hex(0x2E2E2E)
        GRAY_05 = lv.color_hex(0x2A2A2A)

        WHITE_01 = lv.color_hex(0xFFFFFF)
        WHITE_02 = lv.color_hex(0xDDDDDD)

        RED_01 = lv.color_hex(0xF04349)

        GREEN_01 = lv.color_hex(0x28B870)

    BTN_YES_BG = colors.WHITE_01
    BTN_YES_FG = colors.BLACK_01

    BTN_YES_DBG = colors.BLACK_02
    BTN_YES_DFG = colors.GRAY_01

    BTN_CANCEL_BG = colors.BLACK_02
    BTN_CANCEL_FG = colors.WHITE_01

    BTN_CANCEL_DBG = colors.BLACK_02
    BTN_CANCEL_DFG = colors.GRAY_01

    SLIDER_BG = lv_colors.UKEY_WHITE_3
    SLIDER_FG = lv_colors.UKEY_BLACK_2
    SLIDER_NODE_FG = lv_colors.UKEY_BLACK_2
    SLIDER_NODE_DFG = colors.WHITE_02

    SLIDER_IINDICATOR_FG = lv_colors.UKEY_RED_1

    SLIDER_INDICATOR_PFG = lv_colors.UKEY_BLACK_2

    CONT_BG = colors.BLACK_02

    CONT_ITEM_BG = colors.BLACK_02
    CONT_ITEM_FG = colors.WHITE_01
    CONT_ITEM_BOARD_BG = lv_colors.UKEY_O_GRAY_2

    CONT_ITEM_SUB_FG = lv_colors.UKEY_GRAY_1
    CONT_ITEM_SUB_BG = lv_colors.UKEY_WHITE_4

    CONT_ITEM_PBG = colors.GRAY_05
    CONT_ITEM_PFG = colors.WHITE_02

    CONT_ITEM_RIGHT_FG = lv_colors.LIGHT_GRAY
    CONT_ITEM_TITLE_FG = colors.WHITE_01
    CONT_ITEM_SUBTITLE_FG = lv_colors.UKEY_O_GRAY_4

    CONT_ITEM_DBG = colors.BLACK_02
    CONT_ITEM_DFG = colors.GRAY_03

    CONT_ITEM_RIGHT_DFG = lv_colors.UKEY_O_GRAY_1
    CONT_ITEM_BLINE = colors.BLACK_03

    CONT_ITEM_CB_BG = colors.BLACK_02
    CONT_ITEM_CB_FG = colors.WHITE_01
    CONT_ITEM_CB_BOARD_FG = colors.GRAY_01

    CONT_ITEM_CB_PBG = colors.WHITE_01
    CONT_ITEM_CB_PFG = colors.BLACK_01

    CONT_ITEM_SW_BG = colors.BLACK_04
    CONT_ITEM_SW_FG = colors.GRAY_01

    CONT_ITEM_SW_PBG = lv_colors.UKEY_GREEN_1

    CONT_ITEM_LINK_FG = lv_colors.UKEY_BLUE_1

    PROCESS_BAR_BG = lv_colors.UKEY_WHITE_1
    PROCESS_BAR_FG = lv_colors.UKEY_BLUE_1

    DTL_TOP_TITLE_FG = lv_colors.UKEY_BLACK_2
    DTL_TITLE_FG = lv_colors.WHITE
    DTL_SUBTITLE_FG = lv_colors.WHITE
    DTL_BG = lv_colors.UKEY_O_BLACK

    DTL_BTIP_FG = lv_colors.UKEY_WHITE_3

    DT_BG = colors.BLACK_01
    DT_TITLE_FG = colors.WHITE_01
    DT_TITLE_TIP_FG = lv_colors.UKEY_GRAY_3
    DT_SUBTITLE_FG = colors.WHITE_02

    DT_CONT_BTN_BG = colors.BLACK_01
    DT_CONT_BTN_FG = colors.WHITE_01

    DT_TEXT_FG = lv_colors.UKEY_GRAY_1
    DT_TIP_FG = lv_colors.UKEY_GRAY_2
    DT_TIP_BG = lv_colors.UKEY_GRAY_3
    DT_DESC_FG = lv_colors.UKEY_GRAY_2

    DT_DIPB_BG = lv_colors.UKEY_O_YELLOW_2

    DT_DIPB_BD = lv_colors.UKEY_O_YELLOW_3

    DT_DIPB_FG = lv_colors.UKEY_O_YELLOW_1

    LIGHT_SETTING_SLIDER_BG = lv_colors.UKEY_BLACK_3
    LIGHT_SETTING_SLIDER_FG = lv_colors.UKEY_WHITE_3

    POWEROFF_BTN_BG = lv_colors.UKEY_O_RED_1
    POWEROFF_BTN_FG = lv_colors.BLACK

    WALLPAPER_BTN_DEL_BG = lv_colors.UKEY_WHITE_1
    WALLPAPER_BTN_DEL_FG = lv_colors.UKEY_O_RED_1

    TURBO_SLIDER_FG1 = lv_colors.UKEY_BLUE_1

    DOT_POINT_BG = lv_colors.UKEY_O_WHITE_4

    DOT_POINT_PBG = lv_colors.UKEY_O_WHITE_4

    NFT_DELETE_BUT = lv_colors.UKEY_RED_1

    KEYBOARD_BG = colors.BLACK_01

    KEYBOARD_KEY_BG = colors.BLACK_04
    KEYBOARD_KEY_FG = colors.WHITE_01

    KEYBOARD_KEY_PBG = colors.GRAY_05
    KEYBOARD_KEY_PFG = colors.WHITE_01

    KEYBOARD_KEY_DBG = colors.BLACK_04
    KEYBOARD_KEY_DFG = colors.GRAY_03

    KEYBOARD_TIP_BG = colors.BLACK_01
    KEYBOARD_TIP_FG = colors.WHITE_01

    KEYBOARD_DEL_BG = colors.RED_01
    KEYBOARD_DEL_FG = colors.WHITE_01

    KEYBOARD_DEL_DBG = colors.BLACK_04
    KEYBOARD_DEL_DFG = colors.GRAY_03

    KEYBOARD_ETR_BG = colors.GREEN_01
    KEYBOARD_ETR_FG = colors.WHITE_01

    KEYBOARD_ETR_DBG = colors.BLACK_04
    KEYBOARD_ETR_DFG = colors.GRAY_03

    INPUT_BG = colors.BLACK_04
    INPUT_FG = colors.WHITE_01

    INPUT_WFG = colors.WHITE_01

    INPUT_BOARDER_FG = colors.BLACK_04

    INPUT_TIP_FG = colors.GRAY_03

    INPUT_ITIP_FG = lv_colors.UKEY_GRAY_1

    OVERLAY_BG = lv_colors.WHITE
    OVERLAY_PROGRESS_BG = lv_colors.UKEY_O_GRAY_3
    OVERLAY_PROGRESS_FG = lv_colors.BLACK

    NUM_BTN_BG = lv_colors.UKEY_O_GRAY_3
    NUM_BTN_FG = lv_colors.WHITE

    NUM_BTN_PBG = lv_colors.UKEY_O_GREEN
    NUM_BTN_PFG = lv_colors.BLACK
    ROLLER_BG = lv_colors.BLACK
    ROLLER_FG = lv_colors.WHITE_2
    ROLLER_BOARD_BG = lv_colors.BLACK

    ROLLER_PBG = lv_colors.UKEY_O_BLACK_1

    NAV_BACK_PBG = colors.GRAY_03

    TEST_FG = lv_colors.UKEY_RED_1
