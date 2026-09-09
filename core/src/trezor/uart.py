import ustruct
from micropython import const
from typing import TYPE_CHECKING

from storage import device
from trezor import config, io, log, loop, motor, utils, workflow
from trezor.lvglui import StatusBar
from trezor.lvglui.scrs.charging import ChargingPromptScr
from trezor.ui import display

from apps import base

if TYPE_CHECKING:
    from trezor.lvglui.scrs.ble import PairCodeDisplay


_PREFIX = const(42330)  # 0xA55A
_FORMAT = ">HHB"
_HEADER_LEN = const(5)
# fmt: off
_CMD_BLE_NAME = _PRESS_SHORT = _USB_STATUS_PLUG_IN = _BLE_STATUS_CONNECTED = _BLE_PAIR_SUCCESS = CHARGE_START = const(1)
_PRESS_LONG = _USB_STATUS_PLUG_OUT = _BLE_STATUS_DISCONNECTED = _BLE_PAIR_FAILED = _CMD_BLE_STATUS = CHARGE_BY_WIRELESS = const(2)
_BTN_PRESS = const(0x20)
_BTN_RELEASE = const(0x40)
# fmt: on
_BLE_STATUS_OPENED = _POWER_STATUS_CHARGING = _CMD_BLE_PAIR_CODE = const(3)
_BLE_STATUS_CLOSED = _CMD_BLE_PAIR_RES = _POWER_STATUS_CHARGING_FINISHED = const(4)
_CMD_NRF_VERSION = const(5)  # ble firmware version
_CMD_DEVICE_CHARGING_STATUS = const(8)
_CMD_BATTERY_STATUS = const(9)
_CMD_SIDE_BUTTON_PRESS = const(10)
_CMD_LED_BRIGHTNESS = const(12)
_CMD_BATTERY_INFO = const(13)
_CMD_BLE_BUILD_ID = const(16)
_CMD_BLE_HASH = const(17)
_CMD_BLE_MAC = const(18)
_POWER_FETCH_MAX_ATTEMPTS = const(30)
CHARING_TYPE = 0  # 1 VIA USB / 2 VIA WIRELESS
# SCREEN: PairCodeDisplay | None = None
PAIR_CODE_SCREEN: PairCodeDisplay | None = None
PAIR_ERROR_SCREEN = None
PAIR_SUCCESS_SCREEN = None
PENDING_PAIR_CODE: str | None = None
PENDING_PAIR_FAILED: bool = False
BLE_ENABLED: bool | None = None
BLE_CTRL = io.BLE()
FLASH_LED_BRIGHTNESS: int | None = None
BUTTON_PRESSING = False
BLE_PAIR_ABORT = False
_BATTERY_FETCH_ATTEMPTS = 0
_CHARGING_FETCH_ATTEMPTS = 0
_CHARGING_STATUS_READY = False
_LOW_BATTERY_SHUTDOWN_REQUESTED = False


def _maybe_auto_power_off_low_battery() -> None:
    global _LOW_BATTERY_SHUTDOWN_REQUESTED

    should_shutdown = (
        utils.BATTERY_CAP == 0
        and utils.POWER_CONNECTED is False
        and utils.USB_CONNECTED is False
    )

    if not should_shutdown:
        if (
            (utils.BATTERY_CAP is not None and utils.BATTERY_CAP > 0)
            or utils.POWER_CONNECTED
            or utils.USB_CONNECTED
        ):
            _LOW_BATTERY_SHUTDOWN_REQUESTED = False
        return

    if _LOW_BATTERY_SHUTDOWN_REQUESTED:
        return

    _LOW_BATTERY_SHUTDOWN_REQUESTED = True
    if __debug__:
        print("Auto power off: battery is 0 and no power/USB is connected")
    ctrl_power_off()


async def handle_fingerprint_data_init():
    from trezor.lvglui.scrs import lv

    while True:
        if (
            config.fingerprint_is_unlocked()
            and not config.fingerprint_data_inited()
            and lv.disp_get_default().inv_p == 0
        ):
            config.fingerprint_data_read()
        if config.fingerprint_data_inited():
            break
        if display.backlight() == 0:
            await loop.sleep(20)
        else:
            await loop.sleep(50)


async def _wait_for_finger_release(fingerprint) -> None:
    from trezor.lvglui.scrs import fingerprints

    while fingerprint.detect():
        if fingerprints.is_unlocked():
            return
        await loop.sleep(100)


def _show_fingerprint_locked_pin() -> None:
    from trezor.lvglui.scrs.lockscreen import LockScreen
    from trezor.lvglui.scrs.pinscreen import InputPin

    pin_wind = InputPin.get_window_if_visible()
    if pin_wind:
        pin_wind.show_fp_failed_prompt(2)
        return

    visible, scr = LockScreen.retrieval()
    if visible and scr is not None:
        scr.request_unlock(InputPin.fingerprint_subtitle(2))


async def handle_fingerprint():
    from trezorio import fingerprint

    from trezor.lvglui.scrs import fingerprints

    global BUTTON_PRESSING
    while True:
        button_blocks_fingerprint = BUTTON_PRESSING and not _lockscreen_is_visible()
        retry_locked = fingerprints.is_retry_locked()
        if any(
            (
                button_blocks_fingerprint,
                utils.is_collecting_fingerprint(),
                display.backlight() == 0,
                not fingerprints.is_available() and not retry_locked,
                fingerprints.is_unlocked(),
            )
        ):
            return
        finger_is_present = fingerprint.detect()
        if not finger_is_present:
            if not fingerprint.sleep():
                await loop.sleep(100)
                continue
            # The finger may touch the sensor while the interrupt is being armed.
            finger_is_present = fingerprint.detect()
        if not finger_is_present:
            state = await loop.wait(io.FINGERPRINT_STATE)
            if __debug__:
                print(f"state == {state}")
        if fingerprints.is_unlocked():
            return
        should_vibrate = True
        while True:
            try:
                if fingerprints.is_unlocked():
                    return
                detected = fingerprint.detect()
                if detected:
                    await loop.sleep(100)
                    if fingerprints.is_unlocked():
                        return
                    if not fingerprint.detect():
                        continue
                    if __debug__:
                        print("finger detected ....")
                    if fingerprints.is_retry_locked():
                        _show_fingerprint_locked_pin()
                        await _wait_for_finger_release(fingerprint)
                        break
                    try:
                        match_id = fingerprint.match()
                        fps = fingerprints.get_fingerprint_list()
                        if match_id not in fps:
                            raise RuntimeError("Fingerprint ID mismatch")
                    except Exception as e:
                        if __debug__:
                            log.exception(__name__, e)
                            print("fingerprint mismatch")
                        warning_level = 0
                        retry_limit_reached = False
                        if isinstance(e, fingerprint.ExtractFeatureFail):
                            warning_level = 4
                        elif isinstance(
                            e, (fingerprint.NoFp, fingerprint.GetImageFail)
                        ):
                            warning_level = 3
                        elif isinstance(e, fingerprint.NotMatch):
                            # increase failed count
                            device.finger_failed_count_incr()
                            failed_count = device.finger_failed_count()
                            retry_limit_reached = failed_count >= utils.MAX_FP_ATTEMPTS
                            if retry_limit_reached:
                                from trezor.lvglui.scrs.pinscreen import InputPin

                                pin_wind = InputPin.get_window_if_visible()
                                if pin_wind:
                                    pin_wind.refresh_fingerprint_prompt()
                                if config.is_unlocked():
                                    config.lock()

                            warning_level = (
                                1 if failed_count < utils.MAX_FP_ATTEMPTS else 2
                            )
                        from trezor.lvglui.scrs.lockscreen import LockScreen
                        from trezor.lvglui.scrs.pinscreen import InputPin

                        pin_wind = InputPin.get_window_if_visible()
                        visible, scr = LockScreen.retrieval()
                        fingerprint_subtitle = InputPin.fingerprint_subtitle(
                            warning_level
                        )
                        if pin_wind:
                            pin_wind.show_fp_failed_prompt(warning_level)
                        elif visible and scr is not None:
                            scr.show_finger_mismatch_anim()
                            scr.show_tips(warning_level)
                            scr.request_unlock(fingerprint_subtitle)
                        if should_vibrate:
                            should_vibrate = False
                            motor.vibrate(motor.ERROR)
                        if retry_limit_reached:
                            await _wait_for_finger_release(fingerprint)
                            break
                        await _wait_for_finger_release(fingerprint)
                        should_vibrate = True
                    else:
                        if __debug__:
                            print(f"fingerprint match {match_id}")
                        # motor.vibrate(motor.SUCCESS)
                        if device.is_passphrase_pin_enabled():
                            device.set_passphrase_pin_enabled(False)
                        # # 1. publish signal
                        if fingerprints.has_takers():
                            if __debug__:
                                print("publish signal")
                            fingerprints.signal_match()
                        else:
                            # 2. unlock
                            res = fingerprints.unlock()
                            if __debug__:
                                print(f"fingerprint unlock result {res}")
                            await base.unlock_device(into_optscreen=True)
                        # await loop.sleep(2000)
                        return
                else:
                    await loop.sleep(100)
                    continue
            except Exception as e:
                if __debug__:
                    log.exception(__name__, e)
                loop.clear()
                return  # pylint: disable=lost-exception


async def handle_usb_state():
    while True:
        try:
            utils.AIRGAP_MODE_CHANGED = False
            usb_state = loop.wait(io.USB_STATE)
            state, enable = await usb_state
            if enable is not None and not device.is_airgap_mode():
                import usb

                usb.bus.connect_ctrl(enable)
                continue

            utils.turn_on_lcd_if_possible()
            if state:
                utils.USB_CONNECTED = True
                # if display.backlight() == 0:
                ChargingPromptScr.get_instance()
                StatusBar.get_instance().show_usb(True)
                # deal with charging state
                StatusBar.get_instance().show_charging(True)
                if utils.BATTERY_CAP is not None:
                    StatusBar.get_instance().set_battery_img(utils.BATTERY_CAP, True)
                motor.vibrate(motor.MEDIUM)
            else:
                utils.USB_CONNECTED = False
                StatusBar.get_instance().show_usb(False)
                # deal with charging state
                StatusBar.get_instance().show_charging()
                if utils.BATTERY_CAP is not None:
                    StatusBar.get_instance().set_battery_img(utils.BATTERY_CAP, False)
                    _request_charging_status()
            if not utils.AIRGAP_MODE_CHANGED:  # not enable or disable airgap mode
                usb_auto_lock = device.is_usb_lock_enabled()
                if usb_auto_lock and device.is_initialized() and config.has_pin():
                    from trezor.lvglui.scrs import fingerprints
                    from trezor.crypto import se_acl16

                    if config.is_unlocked():
                        se_acl16.clear_session()
                        if fingerprints.is_available():
                            fingerprints.lock()
                        else:
                            config.lock()
                        await safe_reloop()
                        await workflow.spawn(utils.internal_reloop())
                # elif not usb_auto_lock and not state:
                #     await safe_reloop(ack=False)
            else:
                utils.AIRGAP_MODE_CHANGED = False
            _maybe_auto_power_off_low_battery()
            base.reload_settings_from_storage()
        except Exception as exec:
            if __debug__:
                log.exception(__name__, exec)
            loop.clear()


async def safe_reloop(ack=True):
    from trezor import wire
    from trezor.lvglui.scrs.homescreen import change_state

    change_state()
    if ack:
        await wire.signal_ack()


async def handle_uart():
    # await fetch_all()
    while True:
        try:
            await process_push()
        except Exception as exec:
            if __debug__:
                log.exception(__name__, exec)
            loop.clear()
            return  # pylint: disable=lost-exception


async def handle_ble_info():
    while True:
        fetch_ble_info()
        await loop.sleep(500)


async def process_push() -> None:

    uart = loop.wait(io.UART | io.POLL_READ)

    response = await uart
    header = response[:_HEADER_LEN]
    prefix, length, cmd = ustruct.unpack(_FORMAT, header)
    if prefix != _PREFIX:
        # unexpected prefix, ignore directly
        return
    value = response[_HEADER_LEN:][: length - 2]
    if __debug__:
        print(f"cmd == {cmd} with value {value} ")
    if cmd == _CMD_BLE_STATUS:
        # 1 connected 2 disconnected 3 opened 4 closed
        await _deal_ble_status(value)
    elif cmd == _CMD_BLE_PAIR_CODE:
        # show six bytes pair code as string
        if __debug__:
            print(f"Bluetooth Pair: {value}")
        workflow.spawn(_deal_ble_pair(value))
    elif cmd == _CMD_BLE_PAIR_RES:
        # paring result 1 success 2 failed
        await _deal_pair_res(value)
    elif cmd == _CMD_DEVICE_CHARGING_STATUS:
        # 1 usb plug in 2 usb plug out 3 charging
        await _deal_charging_state(value)
    elif cmd == _CMD_BATTERY_STATUS:
        # current battery level, 0-100 only effective when not charging
        global _BATTERY_FETCH_ATTEMPTS
        res = ustruct.unpack(">B", value)[0]
        _BATTERY_FETCH_ATTEMPTS = 0
        utils.BATTERY_CAP = res
        StatusBar.get_instance().set_battery_img(res, utils.CHARGING)
        _maybe_auto_power_off_low_battery()
    elif cmd == _CMD_SIDE_BUTTON_PRESS:
        # 1 short press 2 long press
        await _deal_button_press(value)
    elif cmd == _CMD_BLE_NAME:
        # retrieve ble name has format: ^T[0-9]{4}$
        _retrieve_ble_name(value)
    elif cmd == _CMD_NRF_VERSION:
        # retrieve nrf version
        _retrieve_nrf_version(value)
    elif cmd == _CMD_LED_BRIGHTNESS:
        # LED is managed locally by STM32/camera now, ignore BLE brightness reports.
        pass
    elif cmd == _CMD_BATTERY_INFO:
        _deal_battery_info(value)
    elif cmd == _CMD_BLE_BUILD_ID:
        _retrieve_ble_build_id(value)
    elif cmd == _CMD_BLE_HASH:
        _retrieve_ble_hash(value)
    elif cmd == _CMD_BLE_MAC:
        _retrieve_ble_mac(value)
    else:
        if __debug__:
            print("unknown or not care command:", cmd)


def _clear_pairing_screens():
    """Clear existing pairing-related screens."""
    global PAIR_CODE_SCREEN, PAIR_SUCCESS_SCREEN

    if PAIR_CODE_SCREEN is not None and not PAIR_CODE_SCREEN.destroyed:
        PAIR_CODE_SCREEN.destroy()
        PAIR_CODE_SCREEN = None
    if PAIR_SUCCESS_SCREEN is not None and not PAIR_SUCCESS_SCREEN.destroyed:
        PAIR_SUCCESS_SCREEN.destroy()
        PAIR_SUCCESS_SCREEN = None


async def _display_pair_code(pair_code: str) -> None:
    """Display pair code screen and handle user response."""
    global PAIR_CODE_SCREEN, BLE_PAIR_ABORT

    _clear_pairing_screens()
    utils.turn_on_lcd_if_possible()
    from trezor.lvglui.scrs.ble import PairCodeDisplay

    PAIR_CODE_SCREEN = PairCodeDisplay(pair_code)
    result = await PAIR_CODE_SCREEN.request()

    if result == 0:
        BLE_PAIR_ABORT = True
        _send_pair_code_response(False, None)
    elif result == 1:
        _send_pair_code_response(True, pair_code)


async def _show_pending_pair_code():
    """Display pending pair code if available and not failed."""
    global PAIR_CODE_SCREEN, PENDING_PAIR_CODE, PENDING_PAIR_FAILED

    if PENDING_PAIR_CODE is None:
        return

    if PENDING_PAIR_FAILED:
        PENDING_PAIR_CODE = None
        PENDING_PAIR_FAILED = False
        return

    pair_code = PENDING_PAIR_CODE
    PENDING_PAIR_CODE = None
    PENDING_PAIR_FAILED = False

    await _display_pair_code(pair_code)


async def _deal_ble_pair(value):
    from trezor.qr import close_camera

    close_camera()
    flashled_close()

    if not device.is_initialized():
        from trezor.lvglui.scrs.ble import PairForbiddenScreen

        PairForbiddenScreen()
        return
    # global BLE_PAIR_ABORT
    global BLE_PAIR_ABORT, PAIR_ERROR_SCREEN, PENDING_PAIR_CODE, PENDING_PAIR_FAILED
    BLE_PAIR_ABORT = False

    if not base.device_is_unlocked():
        try:
            await base.unlock_device()
        except Exception:
            await safe_reloop()
            workflow.spawn(utils.internal_reloop())
            return
        else:
            if BLE_PAIR_ABORT:
                return

    # global SCREEN
    # pair_codes = value.decode("utf-8")
    # # pair_codes = "".join(list(map(lambda c: chr(c), ustruct.unpack(">6B", value))))
    # utils.turn_on_lcd_if_possible()
    # from trezor.lvglui.scrs.ble import PairCodeDisplay
    pair_code = value.decode("utf-8")

    if PAIR_ERROR_SCREEN is not None and not PAIR_ERROR_SCREEN.destroyed:
        PENDING_PAIR_CODE = pair_code
        PENDING_PAIR_FAILED = False
        # A new pairing request should replace the stale error popup immediately.
        # PairFailedScreen.destroy() will pick up PENDING_PAIR_CODE and show it.
        PAIR_ERROR_SCREEN.destroy(0)
        return

    if PENDING_PAIR_FAILED and PENDING_PAIR_CODE == pair_code:
        PENDING_PAIR_CODE = None
        PENDING_PAIR_FAILED = False
        return

    PENDING_PAIR_CODE = None
    PENDING_PAIR_FAILED = False

    # SCREEN = PairCodeDisplay(pair_codes)
    await _display_pair_code(pair_code)


_shutdown_task = None
_lock_tip_task = None
_press_start_time = 0
_press_started_on_lockscreen = False


def _hide_lock_tips() -> None:
    StatusBar.get_instance().show_lock_tips(False)


async def _lock_tip_monitor():
    await loop.sleep(1000)
    if not BUTTON_PRESSING:
        return
    if (
        not display.backlight()
        or utils.is_initialization_processing()
        or utils.is_collecting_fingerprint()
        or not device.is_initialized()
        or not config.has_pin()
        or not config.is_unlocked()
    ):
        return
    if __debug__:
        print("Showing lock tips after 1s long press")
    StatusBar.get_instance().show_lock_tips(True)


async def _shutdown_monitor():
    """5-second long-press shutdown monitoring coroutine"""
    await loop.sleep(3000)
    from trezor.lvglui.scrs.homescreen import PowerOff
    from trezor.qr import close_camera

    _hide_lock_tips()
    close_camera()
    PowerOff(
        True
        if not utils.is_initialization_processing() and device.is_initialized()
        else False
    )
    await loop.sleep(200)
    utils.lcd_resume()


def _can_navigate_home() -> bool:
    if utils.is_collecting_fingerprint():
        if __debug__:
            print("Skip home navigation: collecting fingerprint")
        return False
    if utils.is_initialization_processing():
        if __debug__:
            print("Skip home navigation: initialization processing")
        return False
    if not device.is_initialized():
        if __debug__:
            print("Skip home navigation: device not initialized")
        return False
    return True


def _navigate_home_via_back_buttons() -> bool:
    if not _can_navigate_home():
        return False

    from trezor.lvglui.scrs import lv

    handled = False
    for scr in utils.SCREENS[::-1]:
        has_nav_back = hasattr(scr, "nav_back")
        has_is_visible = hasattr(scr, "is_visible")
        is_visible = has_is_visible and scr.is_visible()
        if __debug__:
            print(f"scr: {has_nav_back} {has_is_visible} {is_visible}")
        if has_nav_back and is_visible and hasattr(scr.nav_back, "nav_btn"):
            if __debug__:
                print(f"Found screen with nav_back: {scr.__class__.__name__}")
            lv.event_send(scr.nav_back.nav_btn, lv.EVENT.CLICKED, None)
            handled = True
        if hasattr(scr, "__class__") and hasattr(scr.__class__, "__name__"):
            if __debug__:
                print(f"scr.__class__.__name__: {scr.__class__.__name__}")

    if __debug__ and not handled:
        print("No visible screen with nav_back found")
    return handled


def _trigger_lockscreen_unlock() -> bool:
    from trezor.lvglui.scrs.lockscreen import LockScreen

    visible, screen = LockScreen.retrieval()
    if not visible or screen is None:
        return False

    screen.request_unlock()
    import storage.cache

    storage.cache.start_session()
    return True


def _lockscreen_is_visible() -> bool:
    from trezor.lvglui.scrs.lockscreen import LockScreen

    visible, _ = LockScreen.retrieval()
    return visible


async def _deal_button_press(value: bytes) -> None:
    global _press_start_time
    global _press_started_on_lockscreen
    global _shutdown_task
    global _lock_tip_task
    global BUTTON_PRESSING
    res = ustruct.unpack(">B", value)[0]

    if res in (_PRESS_SHORT, _PRESS_LONG):
        flashled_close()
        if utils.is_collecting_fingerprint():
            return

    if res == _PRESS_SHORT:
        pass

    elif res == _PRESS_LONG:
        pass

    elif res == _BTN_PRESS:
        BUTTON_PRESSING = True
        _press_started_on_lockscreen = _lockscreen_is_visible()
        if __debug__:
            print(f"Home Pressed _press_start_time: {_press_start_time} ")
        import utime

        _press_start_time = utime.ticks_ms()
        if utils.is_collecting_fingerprint():
            from trezor.lvglui.scrs.fingerprints import CollectFingerprintProgress

            if CollectFingerprintProgress.has_instance():
                CollectFingerprintProgress.get_instance().prompt_tips()
                return

        # Cancel the previous shutdown task (if any)
        if _shutdown_task:
            _shutdown_task.close()

        if _lock_tip_task:
            _lock_tip_task.close()
        _hide_lock_tips()

        # 5-second shutdown monitoring upon startup
        _shutdown_task = loop.spawn(_shutdown_monitor())
        _lock_tip_task = loop.spawn(_lock_tip_monitor())

    elif res == _BTN_RELEASE:
        # Button released
        BUTTON_PRESSING = False
        press_started_on_lockscreen = _press_started_on_lockscreen
        _press_started_on_lockscreen = False

        # Cancel the previous shutdown task (if any)
        if _shutdown_task:
            _shutdown_task.close()
            _shutdown_task = None

        if _lock_tip_task:
            _lock_tip_task.close()
            _lock_tip_task = None
        _hide_lock_tips()

        # Calculate press duration
        import utime

        press_duration = utime.ticks_diff(utime.ticks_ms(), _press_start_time)
        if __debug__:
            print(f"Press duration: {press_duration}ms")

        if press_duration < 1000:
            if not display.backlight():
                utils.turn_on_lcd_if_possible()
                return

            if press_started_on_lockscreen:
                _trigger_lockscreen_unlock()
                return

            if _trigger_lockscreen_unlock():
                return

            _navigate_home_via_back_buttons()

        # Determine whether it is a long press (between 1 and 5 seconds).
        elif 1000 <= press_duration < 3000:
            # Execute the screen-off logic
            if display.backlight():
                display.backlight(0)
                if device.is_initialized():
                    if utils.is_initialization_processing():
                        return
                    utils.AUTO_POWER_OFF = True
                    utils.RESTART_MAIN_LOOP = True
                    from trezor.lvglui.scrs import fingerprints

                    if config.has_pin() and config.is_unlocked():
                        from trezor.crypto import se_acl16

                        # TODO: dev se_acl16
                        se_acl16.clear_session()

                        if fingerprints.is_available():
                            if fingerprints.is_unlocked():
                                fingerprints.lock()
                        else:
                            config.lock()
                    await loop.race(safe_reloop(), loop.sleep(200))
                    await loop.sleep(300)
                    workflow.spawn(utils.internal_reloop())
                    base.set_homescreen()
        elif press_duration >= 5000:
            if __debug__:
                print("Super long press (>=5s) - PowerOff already triggered")

        # Reset the press start time
        _press_start_time = 0


def _update_power_connected_from_charging_state(res: int) -> bool:
    if res in (CHARGE_START, _POWER_STATUS_CHARGING):
        power_connected = True
    elif res in (_USB_STATUS_PLUG_OUT, _POWER_STATUS_CHARGING_FINISHED):
        power_connected = False
    else:
        return False

    previous_power_connected = utils.POWER_CONNECTED
    utils.POWER_CONNECTED = power_connected
    return (
        previous_power_connected is not None
        and previous_power_connected != power_connected
    )


async def _deal_charging_state(value: bytes) -> None:
    """THIS DOESN'T WORK CORRECT DUE TO THE PUSHED STATE, ONLY USED AS A FALLBACK WHEN
    CHARGING WITH A CHARGER NOW.

    """
    global CHARING_TYPE, _CHARGING_FETCH_ATTEMPTS, _CHARGING_STATUS_READY
    res, CHARING_TYPE = ustruct.unpack(">BB", value)
    _CHARGING_FETCH_ATTEMPTS = 0
    _CHARGING_STATUS_READY = True
    power_connected_changed = _update_power_connected_from_charging_state(res)

    if res in (
        CHARGE_START,
        _POWER_STATUS_CHARGING,
    ):
        StatusBar.get_instance().show_charging(True)
        if utils.BATTERY_CAP is not None:
            StatusBar.get_instance().set_battery_img(utils.BATTERY_CAP, True)
        if CHARING_TYPE == CHARGE_BY_WIRELESS:

            if utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_STOP:
                utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_CHARGE_STARTING
                fetch_battery_temperature()
                loop.schedule(base.screen_off_delay())
            elif utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STOPPING:
                utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_CHARGE_STARTING
                if display.backlight() > 0:
                    loop.schedule(base.screen_off_delay())
                return
            elif utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STARTING:
                motor.vibrate(motor.MEDIUM)
                return
            elif utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGING:
                return
        else:
            if utils.CHARGING:
                return
            utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_STOP
            ctrl_charge_switch(True)
            utils.CHARGING = True
    elif res in (_USB_STATUS_PLUG_OUT, _POWER_STATUS_CHARGING_FINISHED):
        utils.CHARGING = False
        ctrl_charge_switch(False)
        StatusBar.get_instance().show_charging(False)
        StatusBar.get_instance().show_usb(False)
        if utils.BATTERY_CAP is not None:
            StatusBar.get_instance().set_battery_img(utils.BATTERY_CAP, False)

        if utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGING:
            utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_STOP

        elif utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STARTING:
            utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_CHARGE_STOPPING
            return
        elif utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STOPPING:
            return
            # utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_STOP

    if power_connected_changed:
        utils.turn_on_lcd_if_possible()
    _maybe_auto_power_off_low_battery()


async def _deal_pair_res(value: bytes) -> None:
    res = ustruct.unpack(">B", value)[0]
    if res not in [_BLE_PAIR_SUCCESS, _BLE_PAIR_FAILED]:
        return

    global PAIR_CODE_SCREEN
    if PAIR_CODE_SCREEN is not None and not PAIR_CODE_SCREEN.destroyed:
        PAIR_CODE_SCREEN.destroy()
        PAIR_CODE_SCREEN = None

    if res == _BLE_PAIR_FAILED:
        global BLE_PAIR_ABORT, PENDING_PAIR_CODE, PENDING_PAIR_FAILED, PAIR_ERROR_SCREEN
        BLE_PAIR_ABORT = True
        motor.vibrate(motor.ERROR)
        StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_ENABLED)

        if device.is_initialized():
            if PENDING_PAIR_CODE is not None:
                PENDING_PAIR_FAILED = True
            if PAIR_ERROR_SCREEN is None or PAIR_ERROR_SCREEN.destroyed:
                from trezor.ui.layouts import show_pairing_error

                workflow.spawn(show_pairing_error())
    else:
        motor.vibrate(motor.SUCCESS)
        if device.is_initialized():
            from trezor.ui.layouts import show_pairing_success

            workflow.spawn(show_pairing_success())


async def _deal_ble_status(value: bytes) -> None:
    global BLE_ENABLED
    res = ustruct.unpack(">B", value)[0]
    if res == _BLE_STATUS_CONNECTED:
        utils.BLE_CONNECTED = True
        # show icon in status bar
        utils.turn_on_lcd_if_possible(2 * 60 * 1000)
        StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_CONNECTED)
    elif res == _BLE_STATUS_DISCONNECTED:
        utils.BLE_CONNECTED = False
        if not BLE_ENABLED:
            return
        StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_ENABLED)
        await safe_reloop()
    elif res == _BLE_STATUS_OPENED:
        BLE_ENABLED = True
        if utils.BLE_CONNECTED:
            return
        StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_ENABLED)
        if config.is_unlocked():
            device.set_ble_status(enable=True)
    elif res == _BLE_STATUS_CLOSED:
        utils.BLE_CONNECTED = False
        if not device.is_initialized():
            StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_ENABLED)
            ctrl_ble(True)
            return
        BLE_ENABLED = False
        StatusBar.get_instance().show_ble(StatusBar.BLE_STATE_DISABLED)
        if config.is_unlocked():
            device.set_ble_status(enable=False)


def _deal_battery_info(value: bytes) -> None:
    res, val = ustruct.unpack(">BH", value)
    if res == 4:
        if (
            val <= 38
            and display.backlight() == 0
            and utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STARTING
        ):
            utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_CHARGING
            ctrl_charge_switch(True)
        utils.BATTERY_TEMP = val


def _retrieve_ble_name(value: bytes) -> None:
    if value != b"":
        utils.BLE_NAME = value.decode("utf-8")
        # if config.is_unlocked():
        #     device.set_ble_name(BLE_NAME)


def _retrieve_nrf_version(value: bytes) -> None:
    if value != b"":
        utils.BLE_VERSION = value.decode("utf-8")
        # if config.is_unlocked():
        #     device.set_ble_version(utils.BLE_VERSION)


def _retrieve_ble_build_id(value: bytes) -> None:
    if value != b"":
        utils.BLE_BUILD_ID = value.decode("utf-8")


def _retrieve_ble_hash(value: bytes) -> None:
    if value != b"":
        utils.BLE_HASH = value


def _retrieve_ble_mac(value: bytes) -> None:
    if value != b"":
        utils.BLE_MAC = value


def _request_ble_name():
    """Request ble name."""
    BLE_CTRL.ctrl(0x83, b"\x01")


def _request_ble_version():
    """Request ble version."""
    BLE_CTRL.ctrl(0x83, b"\x02")


def _request_battery_level():
    """Request battery level."""
    BLE_CTRL.ctrl(0x82, b"\x04")


def _request_ble_status():
    """Request current ble status."""
    BLE_CTRL.ctrl(0x81, b"\x04")


def _request_charging_status():
    """Request charging status."""
    BLE_CTRL.ctrl(0x82, b"\x05")


def disconnect_ble():
    if utils.BLE_CONNECTED:
        BLE_CTRL.ctrl(0x81, b"\x03")


async def fetch_all():
    """Request some important data."""
    global _BATTERY_FETCH_ATTEMPTS, _CHARGING_FETCH_ATTEMPTS
    if utils.BATTERY_CAP is None:
        _BATTERY_FETCH_ATTEMPTS = 0
    if not _CHARGING_STATUS_READY:
        _CHARGING_FETCH_ATTEMPTS = 0

    while True:
        if display.backlight():
            flashled_close()
            _request_ble_name()
            _request_ble_version()
            _request_ble_status()
            _request_battery_level()
            _request_charging_status()
            return
        await loop.sleep(100)


def fetch_ble_info():
    if not utils.BLE_NAME:
        BLE_CTRL.ctrl(0x83, b"\x01")

    if utils.BLE_VERSION is None:
        BLE_CTRL.ctrl(0x83, b"\x02")

    global BLE_ENABLED
    if BLE_ENABLED is None:
        BLE_CTRL.ctrl(0x81, b"\x04")

    if utils.BLE_CONNECTED is None:
        BLE_CTRL.ctrl(0x81, b"\x05")

    if utils.BLE_BUILD_ID is None:
        BLE_CTRL.ctrl(0x83, b"\x05")

    if utils.BLE_HASH is None:
        BLE_CTRL.ctrl(0x83, b"\x06")

    if utils.BLE_MAC is None:
        BLE_CTRL.ctrl(0x83, b"\x07")

    global _BATTERY_FETCH_ATTEMPTS, _CHARGING_FETCH_ATTEMPTS
    if (
        utils.BATTERY_CAP is None
        and _BATTERY_FETCH_ATTEMPTS < _POWER_FETCH_MAX_ATTEMPTS
    ):
        _request_battery_level()
        _BATTERY_FETCH_ATTEMPTS += 1

    if (
        not _CHARGING_STATUS_READY
        and _CHARGING_FETCH_ATTEMPTS < _POWER_FETCH_MAX_ATTEMPTS
    ):
        _request_charging_status()
        _CHARGING_FETCH_ATTEMPTS += 1


def fetch_battery_temperature():
    BLE_CTRL.ctrl(0x86, b"\x04")
    # BLE_CTRL.ctrl(0x86, b"\x05")


def ctrl_ble(enable: bool) -> None:
    """Request to open or close ble.
    @param enable: True to open, False to close
    """
    if enable:
        BLE_CTRL.ctrl(0x81, b"\x01")
    else:
        BLE_CTRL.ctrl(0x81, b"\x02")


def flashled_open() -> None:
    """Request to open led."""
    utils.FLASH_LED_BRIGHTNESS = 15
    from trezorio import camera

    camera.flashled(True)


def flashled_close() -> None:
    """Request to close led."""
    utils.FLASH_LED_BRIGHTNESS = 0
    from trezorio import camera

    camera.flashled(False)


def is_flashled_opened() -> bool:
    """Check if led is opened."""
    return bool(utils.FLASH_LED_BRIGHTNESS and utils.FLASH_LED_BRIGHTNESS > 0)


def _send_pair_code_response(accepted: bool, passkey: str | None) -> None:
    if accepted and passkey:
        passkey_bytes = passkey.encode("utf-8")
        BLE_CTRL.ctrl(0x81, b"\x06" + passkey_bytes)
    else:
        BLE_CTRL.ctrl(0x81, b"\x07")


def ctrl_power_off() -> None:
    """Request to power off the device."""
    BLE_CTRL.ctrl(0x82, b"\x01")


def get_ble_name() -> str:
    """Get ble name."""
    return utils.BLE_NAME if utils.BLE_NAME else ""


def get_ble_version() -> str:
    """Get ble version."""
    if utils.EMULATOR:
        return "1.0.0"
    return utils.BLE_VERSION if utils.BLE_VERSION else ""


def get_ble_build_id() -> str:
    return utils.BLE_BUILD_ID if utils.BLE_BUILD_ID else ""


def get_ble_hash() -> bytes:
    return utils.BLE_HASH if utils.BLE_HASH else b""


def get_ble_mac() -> bytes:
    """Get ble MAC address."""
    return utils.BLE_MAC if utils.BLE_MAC else b""


def is_ble_opened() -> bool:
    return BLE_ENABLED if BLE_ENABLED is not None else True


def ctrl_charge_switch(enable: bool) -> None:
    """Request to open or close charge.
    @param enable: True to open, False to close
    """
    if enable:
        if utils.CHARGE_ENABLE is None or not utils.CHARGE_ENABLE:
            BLE_CTRL.ctrl(0x82, b"\x06")
            utils.CHARGE_ENABLE = True
    else:
        if utils.CHARGE_ENABLE is None or utils.CHARGE_ENABLE:
            BLE_CTRL.ctrl(0x82, b"\x07")
            utils.CHARGE_ENABLE = False


def ctrl_wireless_charge(enable: bool) -> None:
    """Request to open or close charge.
    @param enable: True to open, False to close
    """
    if utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGING:
        utils.CHARGE_WIRELESS_STATUS = utils.CHARGE_WIRELESS_CHARGE_STARTING
        ctrl_charge_switch(enable)


def get_wireless_charge_status() -> bool:
    if utils.CHARGE_ENABLE:
        return True
    return False


def stop_mode(reset_timer: bool = False):
    disconnect_ble()

    lp_timer_enable = False
    wireless_charge = False

    if utils.CHARGE_WIRELESS_STATUS == utils.CHARGE_WIRELESS_CHARGE_STARTING:
        lp_timer_enable = True
        wireless_charge = True

    utils.enter_lowpower(
        reset_timer, device.get_autoshutdown_delay_ms(), lp_timer_enable
    )
    if wireless_charge:
        fetch_battery_temperature()
