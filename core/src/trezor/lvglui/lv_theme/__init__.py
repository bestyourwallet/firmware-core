from typing import TYPE_CHECKING

import storage.device as storage_device

import lvgl as lv  # type: ignore [Import "lvgl" could not be resolved]

from ..lv_colors import lv_colors
from ..scrs.components.banner import BannerType
from .dark import theme_colors as theme_colors_dark
from .light import theme_colors as theme_colors_light


class lv_theme:
    # theme_str = [THEME_LIGHT, ]# ['light','dark','auto']
    theme_dir = ["light/li_", "dark/da_", "auto_"]
    THEME_LIGHT, THEME_DARK, THEME_AUTO = list(range(3))
    if __debug__:
        print(f"THEMEME_LIGHT: {THEME_LIGHT}")
    # layout = 'small'

    if TYPE_CHECKING:
        theme: int
        colors: type
        # --- Button ---
        BTN_YES_BG: int
        BTN_YES_FG: int
        BTN_YES_DBG: int
        BTN_YES_DFG: int
        BTN_IYES_FG: int
        BTN_CLOSE_BG: int
        BTN_CANCEL_BG: int
        BTN_CANCEL_FG: int
        BTN_CANCEL_DBG: int
        BTN_CANCEL_DFG: int
        # --- Slider ---
        SLIDER_BG: int
        SLIDER_FG: int
        SLIDER_NODE_FG: int
        SLIDER_NODE_DFG: int
        SLIDER_IINDICATOR_FG: int
        SLIDER_INDICATOR_PFG: int
        # --- Container ---
        CONT_BG: int
        CONT_ITEM_BG: int
        CONT_ITEM_FG: int
        CONT_ITEM_BOARD_BG: int
        CONT_ITEM_SUB_FG: int
        CONT_ITEM_SUB_BG: int
        CONT_ITEM_PBG: int
        CONT_ITEM_PFG: int
        CONT_ITEM_RIGHT_FG: int
        CONT_ITEM_TITLE_FG: int
        CONT_ITEM_SUBTITLE_FG: int
        CONT_ITEM_DBG: int
        CONT_ITEM_DFG: int
        CONT_ITEM_RIGHT_DFG: int
        CONT_ITEM_BLINE: int
        CONT_ITEM_CB_BG: int
        CONT_ITEM_CB_FG: int
        CONT_ITEM_CB_BOARD_FG: int
        CONT_ITEM_CB_PBG: int
        CONT_ITEM_CB_PFG: int
        CONT_ITEM_SW_BG: int
        CONT_ITEM_SW_FG: int
        CONT_ITEM_SW_PBG: int
        CONT_ITEM_LINK_FG: int
        # --- Process bar ---
        PROCESS_BAR_BG: int
        PROCESS_BAR_FG: int
        SCAN_PROGRESS_BG: int
        SCAN_PROGRESS_FG: int
        # --- Desktop Lock ---
        DTL_TOP_TITLE_FG: int
        DTL_TITLE_FG: int
        DTL_SUBTITLE_FG: int
        DTL_BG: int
        DTL_BTIP_FG: int
        # --- Desktop ---
        DT_BG: int
        DT_TITLE_FG: int
        DT_TITLE_TIP_FG: int
        DT_SUBTITLE_FG: int
        DT_CONT_BTN_BG: int
        DT_CONT_BTN_FG: int
        DT_TEXT_FG: int
        DT_TIP_FG: int
        DT_TIP_BG: int
        DT_DESC_FG: int
        DT_DIPB_BG: int
        DT_DIPB_BD: int
        DT_DIPB_FG: int
        # --- Settings ---
        LIGHT_SETTING_SLIDER_BG: int
        LIGHT_SETTING_SLIDER_FG: int
        # UPDATE_BTN_BG: int
        # UPDATE_BTN_FG: int
        POWEROFF_BTN_BG: int
        POWEROFF_BTN_FG: int
        # --- Wallpaper ---
        # WALLPAPER_BTN_YES_BG: int
        # WALLPAPER_BTN_YES_FG: int
        WALLPAPER_BTN_DEL_BG: int
        WALLPAPER_BTN_DEL_FG: int
        # # --- Passphrase / Turbo ---
        # PASSPHRASETIPS_SLIDER_FG1: int
        # PASSPHRASETIPS_SLIDER_FG2: int
        TURBO_SLIDER_FG1: int
        # --- Dot / NFT ---
        DOT_POINT_BG: int
        DOT_POINT_PBG: int
        NFT_DELETE_BUT: int
        # --- Keyboard ---
        KEYBOARD_BG: int
        KEYBOARD_KEY_BG: int
        KEYBOARD_KEY_FG: int
        KEYBOARD_KEY_PBG: int
        KEYBOARD_KEY_PFG: int
        KEYBOARD_KEY_DBG: int
        KEYBOARD_KEY_DFG: int
        KEYBOARD_TIP_BG: int
        KEYBOARD_TIP_FG: int
        KEYBOARD_DEL_BG: int
        KEYBOARD_DEL_FG: int
        KEYBOARD_DEL_DBG: int
        KEYBOARD_DEL_DFG: int
        KEYBOARD_ETR_BG: int
        KEYBOARD_ETR_FG: int
        KEYBOARD_ETR_DBG: int
        KEYBOARD_ETR_DFG: int
        # --- Input ---
        INPUT_BG: int
        INPUT_FG: int
        INPUT_WFG: int
        INPUT_BOARDER_FG: int
        INPUT_TIP_FG: int
        INPUT_ITIP_FG: int
        # --- Overlay ---
        OVERLAY_BG: int
        OVERLAY_PROGRESS_BG: int
        OVERLAY_PROGRESS_FG: int
        # --- Number button ---
        NUM_BTN_BG: int
        NUM_BTN_FG: int
        NUM_BTN_PBG: int
        NUM_BTN_PFG: int
        # --- Roller ---
        ROLLER_BG: int
        ROLLER_FG: int
        ROLLER_BOARD_BG: int
        ROLLER_PBG: int
        # --- Navigation ---
        NAV_BACK_PBG: int
        # --- Misc ---
        TEST_FG: int
        ARC_LOADER_BG: int
        ARC_LOADER_FG: int

    @classmethod
    def get_current_theme(cls):
        return cls.theme_dir[cls.theme]

    @classmethod
    def get_current_theme_id(cls):
        return cls.theme

    @classmethod
    def is_dark_theme(cls):
        return cls.theme == cls.THEME_DARK

    @classmethod
    def is_light_theme(cls):
        return cls.theme == cls.THEME_LIGHT

    @classmethod
    def set_theme(cls, theme):
        cls.theme = theme
        if theme == cls.THEME_LIGHT:
            # print("LIGHT")
            for key, value in theme_colors_light.__dict__.items():
                if not key.startswith("__"):
                    setattr(cls, key, value)
        elif theme == cls.THEME_DARK:
            # print("DARK")
            for key, value in theme_colors_dark.__dict__.items():
                if not key.startswith("__"):
                    setattr(cls, key, value)
        else:
            raise ValueError(f"Invalid theme: {theme}")

    @classmethod
    def get_theme(cls):
        return cls.theme

    @classmethod
    def path_suffix(cls, path, default: bool = False, suffix: str | None = ".png"):
        return f"A:/res/{'default/' if default else cls.theme_dir[cls.theme]}{path}{suffix if suffix else ''}"

    @classmethod
    def path(cls, path):
        return cls.path_suffix(path, False, None)

    @classmethod
    def path_png(cls, path):
        return cls.path_suffix(path, False, ".png")

    @classmethod
    def path_default(cls, path):
        return cls.path_suffix(path, True, None)

    @classmethod
    def path_default_png(cls, path):
        return cls.path_suffix(path, True, ".png")

    APP_SUBINFO_BG = lv.color_hex(0x9FA5B3)
    APP_SUBINFO_FG = lv.color_hex(0x9FA5B3)
    APP_INFO_BG = lv_colors.UKEY_O_GRAY_3
    APP_INFO_FG = lv_colors.UKEY_O_GRAY_3
    APP_CORRECT_BG = lv.color_hex(0x28B870)
    APP_CORRECT_FG = lv.color_hex(0x28B870)
    APP_WARNING_BG = lv_colors.UKEY_O_YELLOW
    APP_WARNING_FG = lv_colors.UKEY_O_YELLOW
    APP_ERROR_BG = lv.color_hex(0xF04349)
    APP_ERROR_FG = lv.color_hex(0xF04349)

    APP_QR_BG = lv_colors.WHITE
    APP_QR_FG = lv_colors.BLACK

    APP_COMP_FG = lv_colors.WHITE
    APP_WHITE_FG = lv_colors.WHITE
    APP_BLACK_FG = lv_colors.BLACK
    APP_BLUE_FG = lv.color_hex(0x4A52FF)

    BOOT_BAR_BG = lv.color_hex(0x222222)
    BOOT_BAR_FG = lv.color_hex(0xEBC562)

    BANNER_STYLE = {
        BannerType.Default: [
            # lv.color_hex(0xF2F3F4),
            lv.color_hex(0x666666),
            "gray",  # banner-icon-gray.png
        ],
        BannerType.DefaultLight: [
            # lv.color_hex(0xEDF6ED),
            lv.color_hex(0x00B51B),
            "green",
        ],
        BannerType.HighLight: [
            # lv.color_hex(0xEDEDF6),
            lv.color_hex(0x4A52FF),
            "blue",
        ],
        BannerType.Warning: [
            # lv.color_hex(0xF6F3ED),
            lv.color_hex(0xEF9C00),
            "yellow",
        ],
        BannerType.Danger: [
            # lv.color_hex(0xF6EDED),
            lv.color_hex(0xF04349),
            "red",
        ],
    }


lv_theme.set_theme(storage_device.get_theme())

if __name__ == "__main__":
    print((lv_theme.BTN_YES_BG))
