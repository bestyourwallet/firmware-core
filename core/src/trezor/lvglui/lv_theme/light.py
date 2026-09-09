import lvgl as lv  # type: ignore [Import "lvgl" could not be resolved]

from ..lv_colors import lv_colors


class theme_colors:
    class colors:
        WHITE_02 = lv.color_hex(0xDDDDDD)
        GRAY_01 = lv.color_hex(0xE0E0E0)
        GRAY_02 = lv.color_hex(0x222222)
        GRAY_03 = lv.color_hex(0xE5E7EA)

    BTN_YES_BG = lv_colors.UKEY_BLACK_2
    BTN_YES_FG = lv_colors.UKEY_WHITE_1

    BTN_YES_DBG = lv_colors.UKEY_O_BLACK_1
    BTN_YES_DFG = lv_colors.UKEY_WHITE_2

    BTN_IYES_FG = lv_colors.UKEY_RED_1

    BTN_CLOSE_BG = lv_colors.UKEY_O_BLACK

    BTN_CANCEL_BG = lv_colors.UKEY_WHITE_8
    BTN_CANCEL_FG = lv_colors.UKEY_BLACK_2

    BTN_CANCEL_DBG = lv_colors.UKEY_WHITE_8
    BTN_CANCEL_DFG = lv_colors.UKEY_GRAY_2

    SCAN_PROGRESS_BG = lv_colors.UKEY_O_GRAY_2
    SCAN_PROGRESS_FG = lv_colors.UKEY_O_GREEN_2

    SLIDER_BG = lv_colors.UKEY_WHITE_3
    SLIDER_FG = lv_colors.UKEY_BLACK_2
    SLIDER_NODE_FG = lv_colors.UKEY_BLACK_2
    SLIDER_NODE_DFG = colors.WHITE_02

    SLIDER_IINDICATOR_FG = lv_colors.UKEY_RED_1

    SLIDER_INDICATOR_PFG = lv_colors.UKEY_BLACK_2

    CONT_BG = lv_colors.UKEY_WHITE_1

    CONT_ITEM_BG = lv_colors.UKEY_WHITE_8
    CONT_ITEM_FG = lv_colors.UKEY_BLACK_2
    CONT_ITEM_BOARD_BG = lv_colors.UKEY_O_GRAY_2

    CONT_ITEM_SUB_FG = lv_colors.UKEY_GRAY_1
    CONT_ITEM_SUB_BG = lv_colors.UKEY_WHITE_4

    CONT_ITEM_PBG = colors.GRAY_03
    CONT_ITEM_PFG = colors.GRAY_02

    CONT_ITEM_RIGHT_FG = lv_colors.LIGHT_GRAY
    CONT_ITEM_TITLE_FG = lv_colors.UKEY_BLACK_1
    CONT_ITEM_SUBTITLE_FG = lv_colors.UKEY_O_GRAY_4

    CONT_ITEM_DBG = lv_colors.UKEY_WHITE_1
    CONT_ITEM_DFG = lv_colors.UKEY_GRAY_2

    CONT_ITEM_RIGHT_DFG = lv_colors.UKEY_O_GRAY_1
    CONT_ITEM_BLINE = lv_colors.UKEY_WHITE_7

    CONT_ITEM_CB_BG = colors.GRAY_01
    CONT_ITEM_CB_FG = colors.GRAY_01
    CONT_ITEM_CB_BOARD_FG = lv_colors.BLACK

    CONT_ITEM_CB_PBG = lv_colors.UKEY_BLACK_1
    CONT_ITEM_CB_PFG = lv_colors.UKEY_WHITE_2

    CONT_ITEM_SW_BG = lv_colors.UKEY_O_GRAY
    CONT_ITEM_SW_FG = lv_colors.UKEY_WHITE_4

    CONT_ITEM_SW_PBG = lv_colors.UKEY_GREEN_1

    CONT_ITEM_LINK_FG = lv_colors.UKEY_BLUE_1

    PROCESS_BAR_BG = lv_colors.UKEY_WHITE_1
    PROCESS_BAR_FG = lv_colors.UKEY_BLUE_1

    DTL_TOP_TITLE_FG = lv_colors.UKEY_BLACK_2
    DTL_TITLE_FG = lv_colors.WHITE
    DTL_SUBTITLE_FG = lv_colors.WHITE
    DTL_BG = lv_colors.UKEY_O_BLACK

    DTL_BTIP_FG = lv_colors.UKEY_WHITE_3

    DT_BG = lv_colors.UKEY_WHITE_3
    DT_TITLE_FG = lv_colors.UKEY_BLACK_2
    DT_TITLE_TIP_FG = lv_colors.UKEY_GRAY_3
    DT_SUBTITLE_FG = lv_colors.UKEY_GRAY_3

    DT_CONT_BTN_BG = lv_colors.UKEY_WHITE_1
    DT_CONT_BTN_FG = lv_colors.UKEY_BLACK_2

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

    ARC_LOADER_BG = lv_colors.UKEY_O_GRAY_2
    ARC_LOADER_FG = lv_colors.BLACK

    KEYBOARD_BG = lv_colors.UKEY_WHITE_3

    KEYBOARD_KEY_BG = lv_colors.UKEY_WHITE_1
    KEYBOARD_KEY_FG = lv_colors.UKEY_BLACK_2

    KEYBOARD_KEY_PBG = colors.GRAY_03
    KEYBOARD_KEY_PFG = lv_colors.UKEY_BLACK_2

    KEYBOARD_KEY_DBG = lv_colors.UKEY_WHITE_1
    KEYBOARD_KEY_DFG = lv_colors.UKEY_GRAY_1

    KEYBOARD_TIP_BG = lv_colors.UKEY_WHITE_2
    KEYBOARD_TIP_FG = lv_colors.UKEY_GRAY_1

    KEYBOARD_DEL_BG = lv_colors.UKEY_RED_1
    KEYBOARD_DEL_FG = lv_colors.WHITE

    KEYBOARD_DEL_DBG = lv_colors.UKEY_WHITE_1
    KEYBOARD_DEL_DFG = lv_colors.UKEY_O_GRAY_1

    KEYBOARD_ETR_BG = lv_colors.UKEY_GREEN_1
    KEYBOARD_ETR_FG = lv_colors.WHITE

    KEYBOARD_ETR_DBG = lv_colors.UKEY_WHITE_1
    KEYBOARD_ETR_DFG = lv_colors.UKEY_O_GRAY_1

    INPUT_BG = lv_colors.UKEY_WHITE_1
    INPUT_FG = lv_colors.UKEY_BLACK_2

    INPUT_WFG = lv_colors.UKEY_BLACK_3

    INPUT_BOARDER_FG = lv_colors.UKEY_WHITE_1

    INPUT_TIP_FG = lv_colors.LIGHT_GRAY

    INPUT_ITIP_FG = lv_colors.UKEY_GRAY_1

    OVERLAY_BG = lv_colors.BLACK
    OVERLAY_PROGRESS_BG = lv_colors.UKEY_O_GRAY_3
    OVERLAY_PROGRESS_FG = lv_colors.WHITE

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
