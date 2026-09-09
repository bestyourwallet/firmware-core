from trezor import utils
from trezor.lvglui.lv_theme import lv_theme

import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]

from ..lv_colors import lv_colors  # noqa: F401
from ..lv_symbols import LV_SYMBOLS  # noqa: F401

theme_path = lv_theme.path
theme_path_png = lv_theme.path_png
theme_path_default = lv_theme.path_default
theme_path_default_png = lv_theme.path_default_png


if utils.EMULATOR:
    font_GeistSemiBold64 = lv.font_load(
        theme_path_default("font_Geist-SemiBold-64-emu.bin")
    )
    font_GeistSemiBold48 = lv.font_load(
        theme_path_default("font_Geist-SemiBold-48-emu.bin")
    )  # only used for number keyboard
    font_GeistSemiBold38 = lv.font_load(
        theme_path_default("font_Geist-SemiBold-38-emu.bin")
    )
    font_GeistSemiBold26 = lv.font_load(
        theme_path_default("font_Geist-SemiBold-26-emu.bin")
    )
    font_GeistSemiBold30 = lv.font_load(
        theme_path_default("font_Geist-SemiBold-30-emu.bin")
    )
    font_GeistRegular30 = lv.font_load(
        theme_path_default("font_Geist-Regular-30-emu.bin")
    )
    font_GeistRegular26 = lv.font_load(
        theme_path_default("font_Geist-Regular-26-emu.bin")
    )
    font_GeistRegular20 = lv.font_load(
        theme_path_default("font_Geist-Regular-20-emu.bin")
    )
    font_GeistMono28 = lv.font_load(
        theme_path_default("font_GeistMono-Regular-28-emu.bin")
    )

else:
    font_GeistSemiBold64 = lv.font_geist_semibold_64
    font_GeistSemiBold48 = lv.font_geist_semibold_48
    font_GeistSemiBold38 = lv.font_geist_semibold_38
    font_GeistSemiBold26 = lv.font_geist_semibold_26
    font_GeistSemiBold30 = lv.font_geist_semibold_30
    font_GeistRegular30 = lv.font_geist_regular_30
    font_GeistRegular26 = lv.font_geist_regular_26
    font_GeistRegular20 = lv.font_geist_regular_20
    font_GeistMono38 = lv.font_geist_mono_38
    font_GeistMono28 = lv.font_geist_mono_28

_COLOR_FLAG: str | None = None


def get_default_wallpaper():
    global _COLOR_FLAG
    if _COLOR_FLAG is None:
        import storage

        serial = storage.device.get_serial()
        color_flag = serial[-1]
        _COLOR_FLAG = color_flag
    if _COLOR_FLAG == "A":  # black shell
        return theme_path_default("wallpaper_1.png")
        # return "A:/res/wallpaper-1.jpg"
    elif _COLOR_FLAG == "B":  # white shell
        return theme_path_default("wallpaper_2.png")
        # return "A:/res/wallpaper-2.jpg"
    else:
        return theme_path_default("wallpaper_1.png")
        # return "A:/res/wallpaper-1.jpg"
