from trezor import utils
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

from .. import lv_theme, theme_path_png
from .common import FullSizeWindow, lv
from .components.container import ContainerFlexCol
from .components.listitem import ListItemWithLeadingCheckbox


class WipeDevice(FullSizeWindow):
    def __init__(self):
        title = _(i18n_keys.TITLE__RESET_DEVICE)
        subtitle = _(i18n_keys.SUBTITLE__RESET_DEVICE)
        confirm_text = _(i18n_keys.BUTTON__SLIDE_TO_RESET)
        cancel_text = _(i18n_keys.BUTTON__CANCEL)
        icon_path = theme_path_png("triangle-warning")
        super().__init__(
            title,
            subtitle,
            confirm_text,
            cancel_text,
            icon_path,
            anim_dir=2,
            hold_confirm=True,
            primary_color=lv_theme.APP_ERROR_BG,
        )
        self.add_nav_back()

    def show_unload_anim(self):
        self.clean()
        self.destroy(100)


class WipeDeviceTips(FullSizeWindow):
    def __init__(self):
        title = _(i18n_keys.TITLE__ERASE_THIS_DEVICE)
        subtitle = _(i18n_keys.SUBTITLE__DEVICE_WIPE_DEVICE_FACTORY_RESET)
        # icon_path = theme_path_png("danger", True)
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__SLIDE_TO_RESET),
            _(i18n_keys.BUTTON__CANCEL),
            # icon_path=icon_path,
            primary_color=lv_theme.APP_ERROR_BG,
            hold_confirm=True,
        )
        self.container = ContainerFlexCol(
            self.content_area,
            self.subtitle,
            padding_row=8,
            clip_corner=False,
        )
        self.item1 = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.CHECK__DEVICE_WIPE_DEVICE_FACTORY_RESET_1),
        )
        self.item2 = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.CHECK__DEVICE_WIPE_DEVICE_FACTORY_RESET_2),
        )
        self.slider_enable(False)
        self.container.add_event_cb(self.on_value_changed, lv.EVENT.VALUE_CHANGED, None)
        self.cb_cnt = 0

    def slider_enable(self, enable: bool = True):
        if enable:
            self.slider.add_flag(lv.obj.FLAG.CLICKABLE)
            self.slider.enable()
        else:
            self.slider.clear_flag(lv.obj.FLAG.CLICKABLE)
            self.slider.enable(False)

    def on_value_changed(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.VALUE_CHANGED:
            if target == self.item1.checkbox:
                if target.get_state() & lv.STATE.CHECKED:
                    self.item1.enable_bg_color()
                    self.cb_cnt += 1
                else:
                    self.item1.enable_bg_color(False)
                    self.cb_cnt -= 1
            elif target == self.item2.checkbox:
                if target.get_state() & lv.STATE.CHECKED:
                    self.item2.enable_bg_color()
                    self.cb_cnt += 1
                else:
                    self.item2.enable_bg_color(False)
                    self.cb_cnt -= 1
            if self.cb_cnt == 2:
                self.slider_enable()
            elif self.cb_cnt < 2:
                self.slider_enable(False)


class WipeDeviceSuccess(FullSizeWindow):
    def __init__(self):
        title = _(i18n_keys.TITLE__RESET_COMPLETE)
        subtitle = _(i18n_keys.SUBTITLE__THE_DEVICE_IS_RESET)
        icon_path = theme_path_png("success")
        confirm_text = _(i18n_keys.BUTTON__RESTART)
        super().__init__(
            title,
            subtitle,
            confirm_text=confirm_text,
            icon_path=icon_path,
            anim_dir=0,
            nav_back=False,
        )

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.btn_yes:
                self.channel.publish(1)
                self.destroy()
            # from apps.base import set_homescreen
            # set_homescreen()


class WipeLiteCardTips(FullSizeWindow):
    def __init__(self):
        is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
        title = _(
            i18n_keys.TITLE__CARD_CONTAINS_BACKUP
            if is_lite
            else i18n_keys.TITLE__RING_CONTAINS_BACKUP
        )
        subtitle = _(i18n_keys.TITLE__CARD_CONTAINS_BACKUP_DESC)
        icon_path = theme_path_png("triangle-warning")
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__OVERWRITE),
            _(i18n_keys.BUTTON__CANCEL),
            icon_path=icon_path,
        )
        self.container = ContainerFlexCol(
            self.content_area,
            self.subtitle,
            padding_row=8,
            clip_corner=False,
        )
        self.item1 = ListItemWithLeadingCheckbox(
            self.container,
            _(i18n_keys.FORM__I_UNDERSTAND_THAT_THE_BACKUP_WILL_BE_OVERWRITTEN),
        )
        self.slider_enable(False)
        self.container.add_event_cb(self.on_value_changed, lv.EVENT.VALUE_CHANGED, None)
        self.cb_cnt = 0

    def slider_enable(self, enable: bool = True):
        if enable:
            self.btn_yes.add_flag(lv.obj.FLAG.CLICKABLE)
            self.btn_yes.enable(
                bg_color=lv_theme.BTN_YES_BG, text_color=lv_theme.BTN_YES_FG
            )

        else:
            self.btn_yes.clear_flag(lv.obj.FLAG.CLICKABLE)
            self.btn_yes.disable(
                bg_color=lv_theme.BTN_YES_DBG, text_color=lv_theme.BTN_YES_DFG
            )

    def on_value_changed(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.VALUE_CHANGED:
            if target == self.item1.checkbox:
                if target.get_state() & lv.STATE.CHECKED:
                    self.item1.enable_bg_color()
                    self.cb_cnt += 1
                else:
                    self.item1.enable_bg_color(False)
                    self.cb_cnt -= 1
            if self.cb_cnt == 1:
                self.slider_enable()
            elif self.cb_cnt < 1:
                self.slider_enable(False)
