from micropython import const
from trezorio import fingerprint

from storage import device
from trezor import config, loop, motor, utils

from ..i18n import gettext as _, keys as i18n_keys
from . import (
    font_GeistRegular30,
    lv,
    lv_theme,
    theme_path,
    theme_path_default,
    theme_path_png,
)
from .common import FullSizeWindow
from .widgets.style import StyleWrapper

FP_TEMPLATE_GROUP_COUNT = const(3)
FP_TEMPLATE_ENROLL_COUNT = const(6)
FP_MAX_COLLECT_COUNT = const(19)
match_chan = loop.chan()


def request():
    return match_chan.take()


def signal_match():
    match_chan.publish(1)


def has_takers():
    return len(match_chan.takers) > 0


def is_available() -> bool:
    return (
        device.is_initialized()
        and device.is_fingerprint_unlock_enabled()
        and config.is_unlocked()
        and has_fingerprints()
        and failed_count() < utils.MAX_FP_ATTEMPTS
    )


def failed_count() -> int:
    return device.finger_failed_count()


def is_retry_locked() -> bool:
    return (
        utils.pin_verified_since_boot()
        and device.is_initialized()
        and device.is_fingerprint_unlock_enabled()
        and failed_count() >= utils.MAX_FP_ATTEMPTS
    )


def get_fingerprint_count() -> int:
    try:
        count = fingerprint.get_template_count()
    except Exception as e:
        if __debug__:
            print(f"get fingerprint count failed: {e}")
        count = 0
    return count


def has_fingerprints() -> bool:
    return get_fingerprint_count() > 0


def should_show_unlock_prompts() -> bool:
    return device.is_fingerprint_unlock_enabled() or has_fingerprints()


def get_fingerprint_list():
    try:
        fingers = fingerprint.list_template()
    except Exception as e:
        if __debug__:
            print(f"get fingerprint list failed: {e}")
        return ()
    return fingers or ()


def get_fingerprint_group() -> bytes:
    return fingerprint.get_group()


def lock() -> bool:
    return config.fingerprint_lock()


def unlock() -> bool:
    return config.fingerprint_unlock()


def is_unlocked() -> bool:
    return config.fingerprint_is_unlocked()


def data_version_is_new() -> bool:
    return fingerprint.data_version_is_new()


def data_upgrade_is_prompted() -> bool:
    return fingerprint.data_upgrade_is_prompted()


def data_upgrade_prompted():
    fingerprint.data_upgrade_prompted()


def get_max_template_count() -> int:
    return fingerprint.get_max_template_count()


def clean_register_cache():
    utils.mark_collecting_fingerprint_done()
    fingerprint.clear_template_cache(True)


class RequestAddFingerprintScreen(FullSizeWindow):
    def __init__(self):
        super().__init__(
            # _(i18n_keys.TITLE__FINGERPRINT),
            None,
            _(i18n_keys.TITLE__FINGERPRINT_DESC),
            _(i18n_keys.BUTTON__ADD_FINGERPRINT),
            _(i18n_keys.BUTTON__NOT_NOW),
            icon_path=theme_path_png("fn_fingerprint"),
            anim_dir=0,
            button_layout=0,
            nav_back=False,
        )
        self.content_area.align(lv.ALIGN.TOP_MID, 0, 100)
        # self.add_nav_back()
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(730, 0)
        # if self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, -190)

    def show_unload_anim(self):
        self.destroy(10)


class FingerprintAddedSuccess(FullSizeWindow):
    def __init__(self):
        super().__init__(
            title=_(i18n_keys.TITLE__FINGERPRINT_ADDED),
            subtitle=_(
                i18n_keys.CONTENT__FINGERPRINT_DATA_IS_PROTECTED_BY_SECURITY_CHIPS
            ),
            confirm_text=_(i18n_keys.BUTTON__DONE),
            anim_dir=0,
            nav_back=False,
        )

        self.title.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.title.text.add_style(StyleWrapper().text_align_center(), 0)
        self.subtitle.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.title.align(lv.ALIGN.TOP_MID, 0, 320)
        self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 16)

        self.btn_yes.add_flag(lv.obj.FLAG.HIDDEN)

        # self.img = lv.img(self.content_area)
        # # self.img.set_src("A:res/icon_success")
        # self.img.set_src(theme_path_png("fn_fn2"))
        # self.img.align(lv.ALIGN.TOP_MID, 0, 111)
        # self.img.add_flag(lv.obj.FLAG.HIDDEN)

        self.gif = lv.gif(self.content_area)
        self.gif.set_src(theme_path("fn_fp-done.gif"))
        self.gif.align(lv.ALIGN.TOP_MID, 0, 100)
        self.gif.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP),
            0,
        )
        self.gif.add_style(StyleWrapper().bg_opa(lv.OPA.TRANSP), lv.PART.MAIN | 0)
        self.gif.set_loop_count(1)
        # self.gif.pause()
        self.gif.add_event_cb(self.on_gif_end, lv.EVENT.READY, None)
        # self.timer = lv.timer_create(lambda t: self.gif.resume(), 300, None)
        # self.timer.set_repeat_count(1)

    def on_gif_end(self, event_obj):
        # self.img.clear_flag(lv.obj.FLAG.HIDDEN)
        self.btn_yes.clear_flag(lv.obj.FLAG.HIDDEN)
        # self.gif.delete()
        # self.timer._del()


class CollectFingerprintStart(FullSizeWindow):
    def __init__(self, title: str, subtitle: str, confirm_text: str, img_path: str):
        super().__init__(
            title=None,
            subtitle=None,  # subtitle,
            confirm_text=confirm_text,
            anim_dir=0,
            # nav_back=False,
        )
        # self.add_nav_back()
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_MOMENTUM)

        # self.title.align_to(self.content_area, lv.ALIGN.TOP_LEFT, 12, 84)
        # self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 16)
        # self.subtitle.set_style_text_letter_space(-2, 0)
        # self.subtitle.align(lv.ALIGN.OUT_BOTTOM_MID, 0, 16)

        # self.content_area.set_style_max_height(720, 0)

        self.img = lv.img(self.content_area)
        self.img.remove_style_all()
        self.img.set_src(img_path)
        self.img.align(lv.ALIGN.TOP_MID, 0, 24)
        # self.img.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 24)

        self.text = lv.label(self.content_area)
        self.text.set_text(subtitle)
        self.text.align_to(self.img, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 21)
        self.text.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular30)
            .width(450)
            .text_color(lv_theme.DT_TITLE_FG)
            .text_letter_space(-2)
            .text_align_center()
            .pad_ver(16)
            .pad_hor(12),
            0,
        )

        self.arrow = lv.img(self.content_area)
        self.arrow.remove_style_all()
        self.arrow.set_src(theme_path_default("tools_finger-start-arrow.png"))
        self.arrow.align_to(self.img, lv.ALIGN.TOP_RIGHT, 0, 260)

        # self.icon_cancel = lv.obj(self.content_area)
        # self.icon_cancel.remove_style_all()
        # self.icon_cancel.set_size(100, 100)
        # self.icon_cancel.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # self.cancel_img = lv.img(self.content_area)
        # self.cancel_img.set_src("A:/res/nav-close.png")
        # self.cancel_img.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # self.icon_cancel.add_flag(lv.obj.FLAG.CLICKABLE)
        # self.icon_cancel.add_event_cb(self.on_close, lv.EVENT.CLICKED, None)

        self.anim = lv.anim_t()
        self.anim.init()
        self.anim.set_var(self.arrow)
        self.anim.set_values(288, 360)
        self.anim.set_time(400)
        self.anim.set_playback_delay(100)
        self.anim.set_playback_time(400)
        self.anim.set_repeat_delay(100)
        self.anim.set_repeat_count(0xFFFF)  # infinite
        self.anim.set_path_cb(lv.anim_t.path_ease_in_out)
        self.anim.set_custom_exec_cb(lambda _a, val: self.anim_set_x(val))
        self.anim_r = lv.anim_t.start(self.anim)

        self.spacer = lv.obj(self.content_area)
        self.spacer.set_size(lv.pct(100), 60)
        self.spacer.align_to(self.img, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
        self.spacer.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self.spacer.set_style_border_width(0, 0)

    # def on_close(self, event_obj):
    #     code = event_obj.code
    #     target = event_obj.get_target()
    #     if code == lv.EVENT.CLICKED:
    #         if target == self.icon_cancel:
    #             self.destroy(0)
    #             self.channel.publish(0)

    def anim_set_x(self, x):
        try:
            self.arrow.set_x(x)
        except Exception:
            lv.anim_del(self.anim_r.var, None)

    def show_unload_anim(self):
        self.destroy(10)


class CollectFingerprintProgress(FullSizeWindow):
    _instance = None

    _SPOT_LOC = [
        (0, 0),
        (5, 20),
        (5, -10),
        (20, -15),
        (30, -20),
        (-30, -30),
        (45, 0),
        (60, 10),
        (30, -60),
        (-60, 28),  # 8
        (-20, -70),  # (-30, -90),
        (70, -10),
        (70, -50),
        (-70, -50),
        (50, 60),
        (-50, 70),
        (-30, 70),
        (-70, 50),
    ]

    @staticmethod
    def get_instance():
        if CollectFingerprintProgress._instance is None:
            CollectFingerprintProgress._instance = CollectFingerprintProgress()
        return CollectFingerprintProgress._instance

    @staticmethod
    def has_instance():
        return CollectFingerprintProgress._instance is not None

    @staticmethod
    def reset():
        CollectFingerprintProgress._instance = None

    def __init__(self):
        super().__init__(
            title="",
            subtitle="",
            anim_dir=0,
        )

        self.img = lv.img(self.content_area)
        self.img.remove_style_all()
        self.img.align(lv.ALIGN.TOP_MID, 0, 156)

        # self.icon_cancel = lv.obj(self.content_area)
        # self.icon_cancel.remove_style_all()
        # self.icon_cancel.set_size(100, 100)
        # self.icon_cancel.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # # self.cancel_img = lv.img(self.content_area)
        # # self.cancel_img.set_src(theme_path_default("nav-close.png"))
        # # self.cancel_img.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # self.icon_cancel.add_flag(lv.obj.FLAG.CLICKABLE)
        # self.icon_cancel.add_event_cb(self.on_close, lv.EVENT.CLICKED, None)

        self.icon_spot = lv.img(self.content_area)
        self.icon_spot.remove_style_all()
        self.icon_spot.add_flag(lv.obj.FLAG.HIDDEN)
        self.icon_spot.set_src(theme_path_default("tools_fingerprint-spot.png"))

        self.tips = lv.label(self.content_area)
        self.tips.set_long_mode(lv.label.LONG.WRAP)
        self.tips.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular30)
            .width(450)
            .text_color(lv_theme.DT_TIP_FG)
            .text_letter_space(-2)
            .text_align_center()
            .pad_ver(16)
            .pad_hor(12),
            0,
        )
        self.tips.align_to(self.content_area, lv.ALIGN.TOP_MID, 0, 450)

    # def on_close(self, event_obj):
    #     code = event_obj.code
    #     target = event_obj.get_target()
    #     if code == lv.EVENT.CLICKED:
    #         if target == self.icon_cancel:
    #             self.channel.publish(0)
    #             self.destroy(50)

    def update_progress(self, progress):
        self.img.set_src(theme_path_png(f"fn_{progress}"))
        x, y = CollectFingerprintProgress._SPOT_LOC[progress]
        self.icon_spot.clear_flag(lv.obj.FLAG.HIDDEN)
        self.icon_spot.align_to(self.img, lv.ALIGN.CENTER, x, y)
        if progress == 0:
            self.tips.set_text(
                _(
                    i18n_keys.MSG__PUT_YOUR_FINGER_ON_THE_POWER_BUTTON_AND_LIFT_IT_AFTERWARDS
                )
            )
        elif progress in range(1, 9) or progress in range(10, 18):
            self.tips.set_text(
                _(
                    i18n_keys.MSG__FOLLOW_THE_ON_SCREEN_GUIDANCE_TO_FINE_TUNE_FINGER_POSITION
                )
            )
        # elif progress in (9, 18):
        #     self.icon_spot.add_flag(lv.obj.FLAG.HIDDEN)
        #     self.tips.add_flag(lv.obj.FLAG.HIDDEN)
        # if progress == 10:
        #     self.icon_spot.clear_flag(lv.obj.FLAG.HIDDEN)
        #     self.tips.clear_flag(lv.obj.FLAG.HIDDEN)

    def prompt_tips(self, text: str | None = None, color: int | None = None):
        if text is None:
            text = _(i18n_keys.MSG__DO_NOT_PRESS_THE_POWER_BUTTON)
        if color is None:
            color = lv_theme.DT_TIP_FG
        self.tips.set_text(text)
        self.tips.set_style_text_color(color, 0)

    def prompt_tips_clear(self):
        self.tips.set_text("")


class FingerprintDataUpgrade(FullSizeWindow):
    def __init__(self, execute_workflow: bool = False):
        super().__init__(
            title=_(i18n_keys.TITLE__FINGERPRINT_UPGRADE),
            subtitle=_(i18n_keys.TITLE__FINGERPRINT_UPGRADE_DESC),
            confirm_text=_(i18n_keys.BUTTON__SET_UP_NOW),
            icon_path=theme_path_png("fn_fn2"),
        )
        # self.icon.align_to(self.content_area, lv.ALIGN.TOP_LEFT, 12, 84)
        # self.title.align_to(self.content_area, lv.ALIGN.TOP_LEFT, 12, 228)
        # self.subtitle.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 16)
        # self.subtitle.set_style_text_letter_space(-2, 0)

        # self.icon_cancel = lv.obj(self.content_area)
        # self.icon_cancel.remove_style_all()
        # self.icon_cancel.set_size(100, 100)
        # self.icon_cancel.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # # self.cancel_img = lv.img(self.content_area)
        # # self.cancel_img.set_src(theme_path_default("nav-close.png"))
        # # self.cancel_img.align(lv.ALIGN.TOP_RIGHT, -12, 12)

        # self.icon_cancel.add_flag(lv.obj.FLAG.CLICKABLE)
        # self.icon_cancel.add_event_cb(self.on_close, lv.EVENT.CLICKED, None)

        self.execute_workflow = execute_workflow

    # def on_close(self, event_obj):
    #     code = event_obj.code
    #     target = event_obj.get_target()
    #     if code == lv.EVENT.CLICKED:
    #         if target == self.icon_cancel:
    #             self.channel.publish(0)
    #             self.destroy(50)

    def show_unload_anim(self):
        from trezor import workflow

        # delete all fingerprints
        fingerprint.clear()
        if self.execute_workflow:
            workflow.spawn(add_fingerprint(0))
        self.destroy(100)


async def request_enroll(i) -> None:
    while fingerprint.detect():
        if __debug__:
            print("move finger away")
        CollectFingerprintProgress.get_instance().prompt_tips(
            _(
                i18n_keys.MSG__LIFT_AND_FINE_TUNE_THE_POSITION_THEN_TOUCH_POWER_BUTTON_AGAIN
            ),
            lv_theme.DT_TIP_FG,
        )
        await loop.sleep(100)
    prompt_text = ""
    CollectFingerprintProgress.get_instance().prompt_tips(
        _(i18n_keys.MSG__FOLLOW_THE_ON_SCREEN_GUIDANCE_TO_FINE_TUNE_FINGER_POSITION),
        lv_theme.DT_TIP_FG,
    )
    should_vibrate = True
    while True:
        if not fingerprint.detect():
            should_vibrate = True
            await loop.sleep(10)
            continue
        try:
            CollectFingerprintProgress.get_instance().prompt_tips(
                _(i18n_keys.MSG__ENROLLING_FINGERPRINT), lv_theme.DT_TIP_FG
            )
            fingerprint.enroll(i)
        except Exception as e:
            if __debug__:
                from trezor import log

                log.exception(__name__, e)
            if should_vibrate:
                should_vibrate = False
                motor.vibrate(motor.WARNING, force=True)
            if isinstance(e, fingerprint.EnrollDuplicate):
                prompt_text = _(
                    i18n_keys.MSG__LIFT_AND_FINE_TUNE_THE_POSITION_THEN_TOUCH_POWER_BUTTON_AGAIN
                )
            elif isinstance(e, fingerprint.ExtractFeatureFail):
                prompt_text = _(i18n_keys.MSG__CLEAN_FINGERPRINT_SENSOR_AND_TRY_AGAIN)
            elif isinstance(e, (fingerprint.NoFp, fingerprint.GetImageFail)):
                prompt_text = _(i18n_keys.MSG__PUT_FINGER_ON_THE_FINGERPRINT)
            if CollectFingerprintProgress.has_instance():
                CollectFingerprintProgress.get_instance().prompt_tips(prompt_text)
            await loop.sleep(10)
        else:
            motor.vibrate(motor.SUCCESS, force=True)
            break


async def request_add_fingerprint() -> None:
    placeholder = FullSizeWindow("", "", anim_dir=0)
    placeholder.set_size(lv.pct(100), lv.pct(100))
    placeholder.add_style(
        StyleWrapper().bg_color(lv_theme.DT_BG).pad_all(0).border_width(0).radius(0), 0
    )
    while True:
        scr = RequestAddFingerprintScreen()
        fp_list = get_fingerprint_list()
        fp_id = 0
        while fp_id in fp_list:
            fp_id += 1
        if fp_id >= get_max_template_count():
            break
        if await scr.request():
            if __debug__:
                print("Adding fingerprint with id:", fp_id)
            success = await add_fingerprint(fp_id)
            if __debug__:
                print("add_fingerprint success:", success)
            if success:
                break
        else:
            break
    placeholder.destroy(0)


async def add_fingerprint(group_id, callback=None) -> bool:

    # current_count = get_fingerprint_count()
    # max_count = get_max_template_count()

    # TODO: DEV fp
    # if max_count == 5 and max_count - current_count < FP_TEMPLATE_GROUP_COUNT:
    #     upgrade_scr = FingerprintDataUpgrade(False)
    #     upgrade_scr.subtitle.set_text(
    #         _(i18n_keys.CONTENT__YOUR_FINGERPRINT_SE_VERSION_IS_OUTDATED)
    #     )
    #     upgrade_scr.btn_yes.add_flag(lv.obj.FLAG.HIDDEN)
    #     await upgrade_scr.request()
    #     return False

    # available_positions = [
    #     index for index, fp in enumerate(get_fingerprint_list()) if fp is None
    # ][:FP_TEMPLATE_GROUP_COUNT]

    placeholder = FullSizeWindow(None, None, anim_dir=0)
    placeholder.set_size(lv.pct(100), lv.pct(100))
    placeholder.add_style(
        StyleWrapper().bg_color(lv_theme.DT_BG).pad_all(0).border_width(0).radius(0), 0
    )
    utils.mark_collecting_fingerprint()
    start_scr = CollectFingerprintStart(
        "",
        _(i18n_keys.UKEY_TITLE__GET_STARTED_DESC),
        _(i18n_keys.BUTTON__START_ENROLL),
        theme_path_png("fn_fn1"),
        # nav_back=False,
    )

    if not await start_scr.request():
        placeholder.destroy(0)
        return False

    progress = None
    success = False
    try:
        progress = CollectFingerprintProgress.get_instance()
        placeholder.destroy(0)
        fingerprint.clear_template_cache(False)
        register_count = 0
        for i in range(0, 19):
            progress.update_progress(i)

            if i == 9:
                # idle = loop.sleep(500)
                # cancel = progress.request()
                # racer = loop.race(idle, cancel)
                # await racer
                # if cancel in racer.finished:
                #     return False

                start_scr = CollectFingerprintStart(
                    "",
                    _(i18n_keys.UKEY_TITLE__ADJUST_YOUR_GRIP_DESC),
                    _(i18n_keys.BUTTON__CONTINUE_ENROLL),
                    theme_path_png("fn_fn1"),
                )
                if not await start_scr.request():
                    return False
                start_scr.destroy(0)
                continue
            elif i == 17:
                # fingerprint.register_template(available_positions[FP_TEMPLATE_GROUP_COUNT - 1])
                fingerprint.register_template(group_id)
                break
            enroll_task = request_enroll(register_count % FP_TEMPLATE_ENROLL_COUNT)
            cancel_task = progress.request()
            racer = loop.race(enroll_task, cancel_task)
            await racer
            if cancel_task in racer.finished:
                return False
            register_count += 1
            # if register_count % FP_TEMPLATE_ENROLL_COUNT == 0:
            #     if not fingerprint.register_template(0):
            #         return False

        # for i in range(FP_MAX_COLLECT_COUNT):
        #     progress.update_progress(i)
        #
        #     if i == 9:
        #         idle = loop.sleep(500)
        #         cancel = progress.request()
        #         racer = loop.race(idle, cancel)
        #         await racer
        #         if cancel in racer.finished:
        #             return False
        #
        #         start_scr = CollectFingerprintStart(
        #             None,
        #             _(i18n_keys.UKEY_TITLE__ADJUST_YOUR_GRIP_DESC),
        #             _(i18n_keys.BUTTON__CONTINUE),
        #             theme_path_png("/fn/fn2")
        #         )
        #         if not await start_scr.request():
        #             return False
        #         start_scr.destroy(0)
        #         continue
        #     elif i == 18:
        #         # fingerprint.register_template(available_positions[FP_TEMPLATE_GROUP_COUNT - 1])
        #         fingerprint.register_template(0)
        #         break
        #     enroll_task = request_enroll(register_count % FP_TEMPLATE_ENROLL_COUNT)
        #     cancel_task = progress.request()
        #     racer = loop.race(enroll_task, cancel_task)
        #     await racer
        #     if cancel_task in racer.finished:
        #         return False
        #     register_count += 1
        #     if register_count % FP_TEMPLATE_ENROLL_COUNT == 0:
        #         if not fingerprint.register_template(0):
        #             return False

        # await loop.sleep(500)
        # if not fingerprint.save(group_id):
        #     return False

        import gc

        gc.collect()
        await FingerprintAddedSuccess().request()
        if callback and callable(callback):
            callback()
        success = True
        return success
    except Exception as e:
        if __debug__:
            print("add_fingerprint exception:", e)
    finally:
        if progress:
            progress.destroy(50)
            CollectFingerprintProgress.reset()
        if not success:
            fingerprint.clear_template_cache(True)
        else:
            motor.vibrate(motor.SUCCESS, force=True)
        utils.mark_collecting_fingerprint_done()
    return False


async def request_delete_fingerprint(fingerprint_name: str, on_remove) -> None:
    confirmed = await RequestRemoveFingerprint(fingerprint_name).request()
    if confirmed:
        confirmed = await ConfirmRemoveFingerprint().request()
        await loop.sleep(20)
        if confirmed:
            await on_remove()


class RequestRemoveFingerprint(FullSizeWindow):
    def __init__(self, fingerprint_name: str):
        super().__init__(
            fingerprint_name,
            None,
            confirm_text=_(i18n_keys.BUTTON__REMOVE),
            icon_path=theme_path_png("fn_fn2"),
        )
        self.add_nav_back()
        self.btn_yes.add_style(StyleWrapper().bg_color(lv_theme.APP_ERROR_BG), 0)

        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.nav_back.nav_btn:
                self.channel.publish(0)
                self.destroy(50)
        elif code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def show_unload_anim(self):
        # if self.anim_dir == ANIM_DIRS.HOR:
        #     Anim(0, -480, self.set_pos, time=200, y_axis=False, delay=200, del_cb=self._delete).start()
        # else:
        #     self.show_dismiss_anim()
        self.destroy(100)


class ConfirmRemoveFingerprint(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__REMOVE_THIS_FINGERPRINT),
            _(i18n_keys.TITLE__REMOVE_THIS_FINGERPRINT_DESC),
            confirm_text=_(i18n_keys.BUTTON__REMOVE),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            icon_path=theme_path_png("fn_fn2"),
        )
        self.add_nav_back()
        self.btn_yes.add_style(StyleWrapper().bg_color(lv_theme.APP_ERROR_BG), 0)
        self.subtitle.add_style(StyleWrapper().text_align_center(), 0)
        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.nav_back.nav_btn:
                self.channel.publish(0)
                self.destroy(50)
        elif code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def show_unload_anim(self):
        self.destroy(10)
