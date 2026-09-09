from storage import device
from trezor import io, log, loop, utils
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs.widgets.style import StyleWrapper

import lvgl as lv  # type: ignore[Import "lvgl" could not be resolved]

from .scrs import lv_theme, theme_path_png

DEFAULT_DISPLAY = None


async def lvgl_tick():
    from trezor import workflow

    inactive_time_bak = 0
    while True:
        if utils.EMULATOR:
            lv.tick_inc(10)
        await loop.sleep(5)
        lv.timer_handler()
        inactive_time = get_elapsed()
        if inactive_time < inactive_time_bak:
            workflow.idle_timer.touch()

        inactive_time_bak = inactive_time


def init_lvgl() -> None:
    import lvgldrv as lcd  # type: ignore[Import "lvgldrv" could not be resolved]

    lv.init()
    if not utils.EMULATOR:
        import stjpeg  # type: ignore[Import "stjpeg" could not be resolved]

        stjpeg.init()
    disp_buf1 = lv.disp_draw_buf_t()
    buf1_1 = lcd.framebuffer(1)
    buf2_2 = lcd.framebuffer(2)
    # disp_buf1.init(buf1_1, buf2_2, len(buf1_1))
    disp_buf1.init(buf1_1, buf2_2, len(buf1_1))
    disp_drv = lv.disp_drv_t()
    disp_drv.init()
    disp_drv.draw_buf = disp_buf1
    disp_drv.flush_cb = lcd.flush
    disp_drv.hor_res = 480
    disp_drv.ver_res = 800
    if buf2_2 is not None:
        disp_drv.full_refresh = True
    # disp_drv.direct_mode = True
    disp_drv.register()

    indev_drv = lv.indev_drv_t()
    indev_drv.init()
    indev_drv.type = lv.INDEV_TYPE.POINTER
    indev_drv.read_cb = lcd.ts_read
    indev_drv.long_press_time = 500
    indev_drv.long_press_repeat_time = 200
    indev_drv.register()


def init_theme() -> None:
    global DEFAULT_DISPLAY
    DEFAULT_DISPLAY = lv.disp_get_default()
    theme = lv.theme_default_init(
        DEFAULT_DISPLAY,
        lv.palette_main(lv.PALETTE.BLUE),
        lv.palette_main(lv.PALETTE.RED),
        True,
        lv.font_default(),
    )
    # dispp.set_bg_color(lv.color_hex(0x000000))
    DEFAULT_DISPLAY.set_theme(theme)


def init_file_system() -> None:
    if not utils.EMULATOR:
        base_dir = "1:/res"

        def clean():
            nonlocal base_dir
            for size, attrs, name in io.fatfs.listdir(f"{base_dir}/wallpapers"):
                if size > 0 and attrs[1] == "h":
                    io.fatfs.unlink(f"{base_dir}/wallpapers/{name}")
            for size, attrs, name in io.fatfs.listdir(f"{base_dir}/nfts/imgs"):
                if size > 0 and attrs[1] == "h":
                    io.fatfs.unlink(f"{base_dir}/nfts/imgs/{name}")
            for size, attrs, name in io.fatfs.listdir(f"{base_dir}/nfts/zooms"):
                if size > 0 and (attrs[1] == "h" or name[:1] == "."):
                    io.fatfs.unlink(f"{base_dir}/nfts/zooms/{name}")
            for size, attrs, name in io.fatfs.listdir(f"{base_dir}/nfts/desc"):
                if size > 0 and (attrs[1] == "h" or name[:1] == "."):
                    io.fatfs.unlink(f"{base_dir}/nfts/desc/{name}")

        io.fatfs.mount()
        # io.fatfs.mkdir("/boot", True)
        # io.fatfs.mkdir("1:/lres", True)
        io.fatfs.mkdir(base_dir, True)
        io.fatfs.mkdir(f"{base_dir}/wallpapers", True)
        io.fatfs.mkdir(f"{base_dir}/nfts", True)
        io.fatfs.mkdir(f"{base_dir}/nfts/imgs", True)
        io.fatfs.mkdir(f"{base_dir}/nfts/zooms", True)
        io.fatfs.mkdir(f"{base_dir}/nfts/desc", True)
        clean()


def get_elapsed() -> int:
    """Get elapsed time since last user activity(e.g. click).
    @return: elapsed time in milliseconds
    """
    # disp = lv.disp_get_default()
    assert DEFAULT_DISPLAY is not None
    return DEFAULT_DISPLAY.get_inactive_time()


try:
    init_file_system()
    init_lvgl()
    init_theme()
    if __debug__:
        log.info("init", "initialized successfully")
except BaseException:
    if __debug__:
        log.error("init", "failed to initialize emulator")


class StatusBar(lv.obj):
    _instance = None

    BLE_STATE_CONNECTED = 0
    BLE_STATE_DISABLED = 1
    BLE_STATE_ENABLED = 2

    DATA_LEN = 7
    (
        BLE_STATUS,
        BLE_SHOW,
        USB_SHOW,
        CHARGING_SHOW,
        BATTERY_VALUE,
        BATTERY_CHARGING,
        AIR_GAP_TIPS_SHOW,
    ) = range(DATA_LEN)

    @classmethod
    def get_instance(cls) -> "StatusBar":
        if cls._instance is None:
            cls._instance = StatusBar()
        return cls._instance

    def __init__(self):
        super().__init__(lv.layer_top())
        self.set_size(lv.pct(100), 44)
        from trezor.lvglui.scrs import font_GeistRegular20

        self.add_style(
            StyleWrapper()
            .border_width(0)
            .text_font(font_GeistRegular20)
            .text_letter_space(-1)
            .text_color(lv_theme.DT_TITLE_FG)
            .bg_opa(lv.OPA.TRANSP)  # TRANSP
            .bg_color(lv_theme.DT_BG)
            .pad_column(0)
            .pad_ver(6)
            .radius(0)
            .pad_hor(4),
            0,
        )
        self.align(lv.ALIGN.TOP_MID, 0, 0)
        self.set_flex_flow(lv.FLEX_FLOW.ROW)
        # align style of the items in the container
        self.set_flex_align(
            lv.FLEX_ALIGN.END, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        # device reset warning
        self.reset_warning = lv.img(self)
        self.reset_warning.set_src(theme_path_png("status_warning"))
        self.reset_warning.add_flag(lv.obj.FLAG.CLICKABLE)
        self.reset_warning.add_flag(lv.obj.FLAG.HIDDEN)
        self.reset_warning.add_event_cb(
            self.on_reset_warning_click, lv.EVENT.CLICKED, None
        )
        if device.is_reset_flag_set():
            self.reset_warning.clear_flag(lv.obj.FLAG.HIDDEN)

        # usb status
        self.usb = lv.img(self)
        self.usb.set_src(theme_path_png("status_usb"))
        self.usb.add_flag(lv.obj.FLAG.HIDDEN)

        # ble status
        ble_enabled = device.ble_enabled()
        self.ble = lv.img(self)
        self.ble.set_src(
            theme_path_png("status_ble-enabled")
            if ble_enabled
            else theme_path_png("status_ble-disabled")
        )

        # battery capacity percent
        self.percent = lv.label(self)
        # self.percent.set_text("null")
        self.percent.add_style(
            StyleWrapper().pad_hor(5).pad_ver(3),
            0,
        )
        self.percent.add_flag(lv.obj.FLAG.HIDDEN)

        # battery capacity icon
        self.battery = lv.img(self)
        self.battery.set_src(theme_path_png("battery_60-white"))
        self.battery.add_flag(lv.obj.FLAG.HIDDEN)
        # charging status
        self.charging = lv.img(self)
        self.charging.set_src(theme_path_png("status_charging"))
        self.charging.add_flag(lv.obj.FLAG.HIDDEN)

        # lock screen tips
        self.lock_tips = lv.img(self)
        self.lock_tips.set_src(theme_path_png("status_lock"))
        self.lock_tips.add_flag(lv.obj.FLAG.FLOATING)
        self.lock_tips.add_flag(lv.obj.FLAG.HIDDEN)
        self.lock_tips.align(lv.ALIGN.LEFT_MID, 4, 0)

        # air gap mode tips
        self.air_gap_tips = lv.label(lv.layer_top())
        self.air_gap_tips.set_text("Air Gap Only")
        self.air_gap_tips.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_color(lv_theme.DT_TITLE_FG)
            .pad_hor(4)
            .pad_ver(0),
            0,
        )
        self.air_gap_tips.align_to(
            self,
            lv.ALIGN.OUT_BOTTOM_LEFT,
            0,
            -((44 - self.air_gap_tips.get_height()) // 2) - 9,
        )
        self.air_gap_tips.add_flag(lv.obj.FLAG.HIDDEN)
        if device.is_airgap_mode():
            self.air_gap_tips.clear_flag(lv.obj.FLAG.HIDDEN)
            self.ble.add_flag(lv.obj.FLAG.HIDDEN)
        self.status = [0] * self.DATA_LEN
        self.security_notice = None

    def show_ble(self, status: int = 0, show: bool = True):
        self.status[self.BLE_STATUS] = status
        self.status[self.BLE_SHOW] = show
        if show:
            if status == StatusBar.BLE_STATE_CONNECTED:
                icon_path = theme_path_png("status_ble-connected")
            elif status == StatusBar.BLE_STATE_ENABLED:
                icon_path = theme_path_png("status_ble-enabled")
            else:
                icon_path = theme_path_png("status_ble-disabled")
            self.ble.set_src(icon_path)
            if self.ble.has_flag(lv.obj.FLAG.HIDDEN) and not device.is_airgap_mode():
                self.ble.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            if not self.ble.has_flag(lv.obj.FLAG.HIDDEN):
                self.ble.add_flag(lv.obj.FLAG.HIDDEN)

    def show_usb(self, show: bool = False):
        self.status[self.USB_SHOW] = show
        if show:
            if self.usb.has_flag(lv.obj.FLAG.HIDDEN):
                self.usb.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            if not self.usb.has_flag(lv.obj.FLAG.HIDDEN):
                self.usb.add_flag(lv.obj.FLAG.HIDDEN)

    def show_charging(self, show: bool = False):
        self.status[self.CHARGING_SHOW] = show
        if show:
            if self.charging.has_flag(lv.obj.FLAG.HIDDEN):
                self.charging.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            if not self.charging.has_flag(lv.obj.FLAG.HIDDEN):
                self.charging.add_flag(lv.obj.FLAG.HIDDEN)

    def set_battery_img(self, value: int, charging: bool):
        self.status[self.BATTERY_VALUE] = value
        self.status[self.BATTERY_CHARGING] = charging
        if charging:
            self.percent.clear_flag(lv.obj.FLAG.HIDDEN)
            self.percent.set_text(f"{min(value, 100)}%")
        else:
            self.percent.add_flag(lv.obj.FLAG.HIDDEN)
        icon_path = retrieve_icon_path(value, charging)
        self.battery.clear_flag(lv.obj.FLAG.HIDDEN)
        self.battery.set_src(icon_path)

    def show_air_gap_mode_tips(self, show: bool = False):
        self.status[self.AIR_GAP_TIPS_SHOW] = show
        if show:
            if self.air_gap_tips.has_flag(lv.obj.FLAG.HIDDEN):
                self.air_gap_tips.clear_flag(lv.obj.FLAG.HIDDEN)
                self.ble.add_flag(lv.obj.FLAG.HIDDEN)
        else:
            if not self.air_gap_tips.has_flag(lv.obj.FLAG.HIDDEN):
                self.air_gap_tips.add_flag(lv.obj.FLAG.HIDDEN)
                self.ble.clear_flag(lv.obj.FLAG.HIDDEN)

    def show_lock_tips(self, show: bool = False):
        self.lock_tips.set_src(theme_path_png("status_lock"))
        self.lock_tips.align(lv.ALIGN.LEFT_MID, 4, 0)
        if show:
            self.lock_tips.clear_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.lock_tips.add_flag(lv.obj.FLAG.HIDDEN)

    def on_reset_warning_click(self, event_obj):
        if utils.lcd_resume():
            return
        from trezor.lvglui.scrs.common import FullSizeWindow

        if self.security_notice is not None:
            return

        self.security_notice = FullSizeWindow(
            _(i18n_keys.TITLE__DEVICE_SECURITY_NOTICE),
            _(i18n_keys.SUBTITLE__DEVICE_SECURITY_NOTICE),
            _(i18n_keys.BUTTON__I_GOT_IT),
            icon_path=theme_path_png("warning-red"),
        )
        self.security_notice.add_event_cb(
            self.on_security_notice_delete, lv.EVENT.DELETE, None
        )

    def on_security_notice_delete(self, event_obj):
        self.security_notice = None

    def get_status(self):
        return self.status

    def update_status(self, status: list[int] | None):
        if status is None:
            return
        self.status = status
        self.show_ble(status[self.BLE_STATUS], bool(status[self.BLE_SHOW]))
        self.show_usb(bool(status[self.USB_SHOW]))
        self.show_charging(bool(status[self.CHARGING_SHOW]))
        self.set_battery_img(
            status[self.BATTERY_VALUE], bool(status[self.BATTERY_CHARGING])
        )
        self.show_air_gap_mode_tips(bool(status[self.AIR_GAP_TIPS_SHOW]))
        self.reset_warning.set_src(theme_path_png("status_warning"))
        self.lock_tips.set_src(theme_path_png("status_lock"))
        self.lock_tips.align(lv.ALIGN.LEFT_MID, 4, 0)
        self.air_gap_tips.add_style(StyleWrapper().text_color(lv_theme.DT_TITLE_FG), 0)
        self.add_style(StyleWrapper().bg_color(lv_theme.DT_BG), 0)


def retrieve_icon_path(value: int, charging: bool) -> str:
    color = "green" if charging else "white"
    for threshold in range(95, -1, -5):
        if value >= threshold:
            return theme_path_png(f"battery_{threshold + 5}-{color}")
    return theme_path_png(f"battery_none-{color}")
