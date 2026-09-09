import gc
import utime

from trezor import motor, utils
from trezor.enums import InputScriptType
from trezor.lvglui.scrs.components.button import NormalButton
from trezor.lvglui.scrs.components.pageable import PageAbleMessage

from ..i18n import gettext as _, keys as i18n_keys
from ..lv_symbols import LV_SYMBOLS
from . import (
    font_GeistMono28,
    font_GeistMono38,
    font_GeistRegular20,
    font_GeistRegular30,
    font_GeistSemiBold26,
    font_GeistSemiBold38,
    font_GeistSemiBold48,
    lv_theme,
    theme_path,
    theme_path_default,
    theme_path_png,
)
from .common import FullSizeWindow, lv
from .components.banner import Banner, BannerType
from .components.button import ListItemBtn
from .components.composite import (
    AmountGroup,
    CardGroup,
    DirectionGroup,
    FeeGroup,
    MoreGroup,
    RawDataItem,
)
from .components.container import ContainerFlexCol
from .components.line import Line
from .components.listitem import CardHeader, CardItem, DisplayItem
from .components.qrcode import QRCode
from .widgets.style import StyleWrapper


class Address(FullSizeWindow):
    class SHOW_TYPE:
        ADDRESS = 0
        QRCODE = 1

    def __init__(
        self,
        title,
        path,
        address,
        primary_color,
        icon_path: str,
        xpubs=None,
        address_qr=None,
        multisig_index: int | None = 0,
        addr_type=None,
        evm_chain_id: int | None = None,
        qr_first: bool = False,
    ):
        ts = icon_path.rsplit(".", 1)
        title_icon_path = f"{ts[0]}-40.{ts[1]}" if len(ts) >= 2 else icon_path
        super().__init__(
            title,
            None,
            confirm_text=_(i18n_keys.BUTTON__DONE),
            cancel_text=_(i18n_keys.BUTTON__QRCODE)
            if not qr_first
            else _(i18n_keys.BUTTON__ADDRESS),
            anim_dir=0,
            primary_color=primary_color,
            button_layout=1,
            title_icon_path=title_icon_path,
        )
        # self.title.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 15, 0)
        # self.title.add_style(StyleWrapper().bg_color(lv_theme.APP_ERROR_BG).bg_opa(lv.OPA.COVER), 0)
        self.path = path
        self.xpubs = xpubs
        self.multisig_index = multisig_index
        self.address = address
        self.address_qr = address_qr
        self.icon = icon_path
        self.addr_type = addr_type
        self.evm_chain_id = evm_chain_id
        if primary_color and title:
            self.title.add_style(StyleWrapper().text_color(primary_color), 0)
        self.qr_first = qr_first
        if qr_first:
            self.show_qr_code()  # self.qr_first)
        else:
            self.show_address(evm_chain_id=evm_chain_id)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

    def show_address(self, evm_chain_id: int | None = None):
        self.current = self.SHOW_TYPE.ADDRESS
        if hasattr(self, "qr"):
            self.qr.delete()
            del self.qr
        if hasattr(self, "subtitle"):
            self.subtitle.delete()
            del self.subtitle
        self.btn_no.label.set_text(_(i18n_keys.BUTTON__QRCODE))

        # self.item_addr = DisplayItem(
        #     self.content_area, None, utils.addr_chunkify(self.address), radius=10
        # )
        # self.item_addr.add_style(
        #     StyleWrapper()
        #     .pad_all(24)
        #     , 0
        # )
        # self.item_addr.label.add_style(
        #     StyleWrapper()
        #     # .text_font(font_GeistSemiBold48)
        #     .text_font(font_GeistMono38)
        #     .text_line_space(-2)
        #     .text_color(lv_theme.CONT_ITEM_FG),
        #     0,
        # )
        self.item_addr = DisplayItem(
            self.content_area,
            None,
            utils.addr_chunkify(self.address),
            font=font_GeistMono38,
            # padding_hor=0,
            label_hor=8,
            radius=10,
        )

        self.item_addr.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 40)

        self.container = ContainerFlexCol(
            self.content_area, self.item_addr, pos=(0, 8), padding_row=0, radius=12
        )
        # self.container.add_dummy()
        if self.addr_type:
            self.item_type = DisplayItem(
                self.container,
                _(i18n_keys.LIST_KEY__TYPE__COLON),
                self.addr_type,
                radius=12,
            )
        if evm_chain_id:
            self.item_chin_id = DisplayItem(
                self.container,
                _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                str(evm_chain_id),
                radius=12,
            )
        self.item_path = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__PATH__COLON),
            self.path,
            radius=10,
            label_hor=0,
        )
        # self.container.add_dummy()
        self.xpub_group = ContainerFlexCol(
            self.content_area,
            self.container,
            pos=(0, 8),
            clip_corner=False,
            radius=12,
        )
        self.xpub_group.add_style(StyleWrapper().bg_opa(lv.OPA.TRANSP), 0)
        for i, xpub in enumerate(self.xpubs or []):
            self.item3 = CardItem(
                self.xpub_group,
                _(i18n_keys.LIST_KEY__XPUB_STR_MINE__COLON).format(i + 1)
                if i == self.multisig_index
                else _(i18n_keys.LIST_KEY__XPUB_STR_COSIGNER__COLON).format(i + 1),
                xpub,
                theme_path_png("group-icon-more"),
            )

    def show_qr_code(self, has_tips: bool = False):
        self.current = self.SHOW_TYPE.QRCODE
        if hasattr(self, "container"):
            self.container.delete()
            del self.container
        if hasattr(self, "xpub_group"):
            self.xpub_group.delete()
            del self.xpub_group
        if hasattr(self, "item_addr"):
            self.item_addr.delete()
            del self.item_addr
        self.btn_no.label.set_text(_(i18n_keys.BUTTON__ADDRESS))
        if has_tips:
            from .components.label import SubTitle

            self.subtitle = SubTitle(
                self.content_area,
                self.title,
                (0, 16),
                _(
                    i18n_keys.CONTENT__RETUNRN_TO_THE_APP_AND_SCAN_THE_SIGNED_TX_QR_CODE_BELOW
                ),
            )
            self.subtitle.set_size(450, lv.SIZE.CONTENT)
        self.qr = QRCode(
            self.content_area,
            self.address if self.address_qr is None else self.address_qr,
            self.icon,
        )
        self.qr.align_to(
            self.title if not has_tips else self.subtitle,
            lv.ALIGN.OUT_BOTTOM_MID,
            0,
            20,
        )

        # print('aaaaaa: ', self.content_area.get_height(), self.content_area.get_width())
        self.content_area.add_style(StyleWrapper().pad_ver(20), 0)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            utils.lcd_resume()
            if target == self.btn_no:
                if self.current == self.SHOW_TYPE.ADDRESS:
                    self.show_qr_code(self.qr_first)
                else:
                    self.show_address(self.evm_chain_id)
            elif target == self.btn_yes:
                self.show_unload_anim()
                self.channel.publish(1)
            elif target in (self.nav_back, self.nav_back.nav_btn):
                self.show_dismiss_anim()
                self.channel.publish(0)


class DeriveConfigScreen(FullSizeWindow):
    def __init__(self, parent, addr_type, derive_options, *, title):
        super().__init__(
            title,
            None,
            confirm_text="",
            cancel_text="",
            anim_dir=2,
        )
        self.parent = parent

        self.add_nav_back()

        self.derive_options = derive_options

        self.container = ContainerFlexCol(self.content_area, self.title, padding_row=2)
        self.container.set_style_bg_opa(lv.OPA.COVER, 0)
        self.selected_type = None
        # Create buttons and set checked state
        self.option_btns = []
        for i, (text, type_value) in enumerate(self.derive_options):
            btn = ListItemBtn(
                self.container,
                text,
                has_next=False,
                bot_line=False if len(self.derive_options) - 1 == i else True,
                use_transition=False,
            )
            btn.add_check_img()
            if text == addr_type:
                btn.set_checked()
                self.selected_type = type_value
            self.option_btns.append(btn)

        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        if code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()

        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return

            if isinstance(target, lv.imgbtn):
                if target in (self.nav_back.nav_btn, self.nav_back):
                    if self.parent is not None:
                        self.parent.on_derive_config_changed(self.selected_type)
                        self.destroy(50)

            else:
                for i, btn in enumerate(self.option_btns):
                    if target == btn:
                        for other_btn in self.option_btns:
                            other_btn.set_uncheck()

                        btn.set_checked()
                        self.selected_type = self.derive_options[i][1]
                        self.parent.on_derive_config_changed(self.selected_type)
                        self.destroy(50)


class ADDRESS_OFFLINE_RETURN_TYPE:
    DONE = 0
    COMMON_DRI_CONFIG_CHANGED = 1
    BTC_DRI_CONFIG_CHANGED = 2


class AddressOffline(FullSizeWindow):
    class SHOW_TYPE:
        ADDRESS = 0
        QRCODE = 1

    def __init__(
        self,
        name,
        index,
        xpubs=None,
        address_qr=None,
        multisig_index: int | None = 0,
        # addr_type=None,
        evm_chain_id: int | None = None,
        qr_first: bool = False,
        # network: str = "",
        prev_scr=None,
        account_name: str = "",
    ):
        from .address import AddressManager

        self.addr_manager = AddressManager(name, index)
        assert self.addr_manager.current_chain_info is not None

        primary_color = lv.color_hex(
            self.addr_manager.current_chain_info["primary_color"]
        )
        icon_path = theme_path_default(
            f"chain_{self.addr_manager.current_chain_info['icon']}-40.png"
        )
        address = ""
        self.current_index = index
        super().__init__(
            name,
            None,
            confirm_text=_(i18n_keys.BUTTON__DONE),
            cancel_text=_(i18n_keys.BUTTON__QRCODE)
            if not qr_first
            else _(i18n_keys.BUTTON__ADDRESS),
            anim_dir=0,
            primary_color=primary_color,
            title_icon_path=icon_path,
            button_layout=1,
            nav_back=True,
        )
        self.xpubs = xpubs
        self.multisig_index = multisig_index
        self.address = address
        self.address_qr = address_qr
        self.icon = icon_path
        self.addr_type = self.addr_manager.addr_type
        self.evm_chain_id = evm_chain_id
        self.network = self.addr_manager.current_chain_info["name"]
        self.prev_scr = prev_scr
        self.account_name = account_name
        if primary_color:
            self.title.add_style(StyleWrapper().text_color(primary_color), 0)
        self.qr_first = qr_first
        self.spinner = lv.spinner(self.content_area, 1000, 60)
        self.spinner.set_size(146, 146)
        # self.spinner.center()
        self.spinner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 150)
        self.spinner.set_style_arc_color(lv_theme.CONT_BG, 0)
        self.spinner.set_style_arc_color(lv_theme.DT_BG, lv.PART.INDICATOR)
        self.spinner.set_style_arc_width(6, 0)
        self.spinner.set_style_arc_width(6, lv.PART.INDICATOR)
        self.spinner.set_style_bg_opa(lv.OPA._50, lv.PART.INDICATOR)
        self.spinner_tip = lv.label(self.content_area)
        self.spinner_tip.set_text(_(i18n_keys.TITLE__PLEASE_WAIT)[:-3])
        # self.spinner_tip.
        self.spinner_tip.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular30)
            .text_color(lv_theme.DT_TIP_FG)
            .text_letter_space(-1),
            0,
        )
        self.spinner_tip.align_to(self.spinner, lv.ALIGN.OUT_BOTTOM_MID, 0, 60)

        # if qr_first:
        #     self.show_qr_code(self.qr_first)
        # else:
        #     self.show_address(evm_chain_id=evm_chain_id)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

        self.address_timer = lv.timer_create(
            lambda t: self._update_address_async(), 1000, None
        )
        self.address_timer.set_repeat_count(1)

    def _update_address_async(self):
        """Asynchronous address update"""
        from trezor import workflow
        from trezor.loop import TaskClosed

        async def update_task():
            try:
                address = await self.addr_manager.chain_address()

                # if not hasattr(self, 'screen_container') or self.screen_container is None:
                #     print("update_task: screen already closed, skipping update")
                #     return

                self.address = address
                self.addr_type = self.addr_manager.addr_type
                if self.address is None or len(self.address) <= 0:
                    self.destroy(50)
                    return
                # print("_update_address_async address:", self.address)
                if self.qr_first:
                    self.show_qr_code(self.qr_first)
                else:
                    self.show_address(evm_chain_id=None)

            except TaskClosed:
                if __debug__:
                    print("update_task: TaskClosed, screen was closed")
            except Exception as e:
                import sys

                sys.print_exception(e)  # type: ignore["print_exception" is not a known member of module]

        workflow.spawn(update_task())

    def clean_show(self):
        if hasattr(self, "qr"):
            self.qr.delete()
            del self.qr
        if hasattr(self, "subtitle"):
            self.subtitle.delete()
            del self.subtitle
        if hasattr(self, "derive_btn"):
            self.derive_btn.delete()
            del self.derive_btn
        if hasattr(self, "group_address"):
            self.group_address.delete()
            del self.group_address
        if hasattr(self, "erc20_tips"):
            self.erc20_tips.delete()
            del self.erc20_tips
        self.spinner.add_flag(lv.obj.FLAG.HIDDEN)
        self.spinner_tip.add_flag(lv.obj.FLAG.HIDDEN)

    def show_address(self, evm_chain_id: int | None = None):
        self.clean_show()
        self.current = self.SHOW_TYPE.ADDRESS
        self.btn_no.label.set_text(_(i18n_keys.BUTTON__QRCODE))
        # derive btn
        if (
            self.network in ("Bitcoin", "Ethereum", "Solana", "Litecoin", "Kaspa")
            and self.addr_type is not None
        ):
            self.derive_btn = ListItemBtn(
                self.content_area,
                self.addr_type,
                left_img_src=theme_path_png("branches"),
                has_next=True,
                min_height=80,
            )

            self.derive_btn.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 40)
            self.derive_btn.set_style_radius(10, 0)
            self.derive_btn.add_style(
                StyleWrapper().bg_opa(lv.OPA.COVER).bg_color(lv_theme.CONT_ITEM_BG),
                0,
            )

            # address
            self.group_address = ContainerFlexCol(
                self.content_area, self.derive_btn, pos=(0, 8), padding_row=0
            )
        else:
            self.group_address = ContainerFlexCol(
                self.content_area,
                self.title,
                lv.ALIGN.OUT_BOTTOM_LEFT,
                pos=(0, 40),
                padding_row=0,
            )
        self.item_group_header = CardHeader(
            self.group_address,
            self.account_name,
            theme_path_png("wallet-02"),
        )
        self.item_group_body = DisplayItem(
            self.group_address,
            None,
            utils.addr_chunkify(self.address),
            font=font_GeistMono38,
            padding_hor=0,
            label_hor=15,
        )

        if self.network == "Ethereum":
            self.erc20_tips = Banner(
                self.content_area,
                BannerType.DefaultLight,
                _(i18n_keys.CONTENT__NETWORK_ADDRESS_ETHEREUM),
            )
            self.erc20_tips.align_to(self.group_address, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)

    def show_qr_code(self, has_tips: bool = False):
        self.clean_show()
        self.current = self.SHOW_TYPE.QRCODE
        self.btn_no.label.set_text(_(i18n_keys.BUTTON__ADDRESS))
        if has_tips:
            from .components.label import SubTitle

            self.subtitle = SubTitle(
                self.content_area,
                self.title,
                (0, 16),
                _(
                    i18n_keys.CONTENT__RETUNRN_TO_THE_APP_AND_SCAN_THE_SIGNED_TX_QR_CODE_BELOW
                ),
            )
            self.subtitle.set_size(465, lv.SIZE.CONTENT)
        self.qr = QRCode(
            self.content_area,
            self.address if self.address_qr is None else self.address_qr,
            self.icon,
        )
        self.qr.align_to(
            self.title if not has_tips else self.subtitle,
            lv.ALIGN.OUT_BOTTOM_MID,
            0,
            30,
        )

    def on_derive_config_changed(self, new_type):
        if self.network in (
            "Bitcoin",
            "Litecoin",
        ):
            self.addr_manager.btc_script_type = new_type
        elif self.network in (
            "Ethereum",
            "Solana",
            "Kaspa",
        ):
            self.addr_manager.use_standard_derivation = new_type
        else:
            raise ValueError(f"Unsupported network: {self.network}")

        self._update_address_async()
        # self.destroy(50)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            utils.lcd_resume()
            if target == self.btn_no:
                if not hasattr(self, "current"):
                    return
                if self.current == self.SHOW_TYPE.ADDRESS:
                    self.show_qr_code(self.qr_first)
                else:
                    self.show_address(self.evm_chain_id)
            elif target == self.btn_yes:
                self.destroy(50)
                self.channel.publish(ADDRESS_OFFLINE_RETURN_TYPE.DONE)
            elif target in (self.nav_back.nav_btn, self.nav_back):
                self.destroy(50)
            elif hasattr(self, "derive_btn") and target == self.derive_btn:
                title = _(i18n_keys.TITLE__SELECT_DERIVATION_PATH)
                if self.network == "Bitcoin":
                    options = [
                        ("Nested Segwit", InputScriptType.SPENDP2SHWITNESS),
                        ("Taproot", InputScriptType.SPENDTAPROOT),
                        ("Native Segwit", InputScriptType.SPENDWITNESS),
                        ("Legacy", InputScriptType.SPENDADDRESS),
                    ]
                elif self.network == "Litecoin":
                    options = [
                        ("Nested Segwit", InputScriptType.SPENDP2SHWITNESS),
                        ("Native Segwit", InputScriptType.SPENDWITNESS),
                        ("Legacy", InputScriptType.SPENDADDRESS),
                    ]
                elif self.network in ("Ethereum", "Solana"):
                    options = [
                        ("BIP44 Standard", True),
                        ("Ledger Live", False),
                    ]
                elif self.network == "Kaspa":
                    options = [
                        (_(i18n_keys.BUTTON_UKEY_EXTENDED), True),
                        (_(i18n_keys.BUTTON_KASPA_OFFICIAL), False),
                    ]
                    title = _(i18n_keys.TITLE__SELECT_ACCOUNT_TYPE)
                else:
                    raise ValueError(f"Unsupported network: {self.network}")
                DeriveConfigScreen(self, self.addr_type, options, title=title)


class XpubOrPub(FullSizeWindow):
    def __init__(
        self, title, path, primary_color, icon_path: str, xpub=None, pubkey=None
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__EXPORT),
            _(i18n_keys.BUTTON__CANCEL),
            anim_dir=2,
            icon_path=icon_path,
            primary_color=primary_color,
            button_layout=1,
        )
        self.title.add_style(StyleWrapper().text_color(primary_color), 0)
        self.item_xpub_or_pub = CardItem(
            self.content_area,
            _(i18n_keys.LIST_KEY__XPUB__COLON)
            if xpub
            else _(i18n_keys.LIST_KEY__PUBLIC_KEY__COLON),
            xpub or pubkey,
            theme_path_png("group-icon-more"),
        )
        self.item_xpub_or_pub.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(
            self.content_area, self.item_xpub_or_pub, pos=(0, 16), padding_row=0
        )
        # self.container.add_dummy()
        self.item_path = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__PATH__COLON), path
        )
        self.item_path.add_style(
            StyleWrapper().radius(10).bg_opa(lv.OPA.TRANSP).border_opa(lv.OPA.TRANSP),
            0,
        )
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(665, 0)
        # if self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

        # self.container.add_dummy()


class Message(FullSizeWindow):
    def __init__(
        self,
        title,
        address,
        message,
        primary_color,
        icon_path,
        verify: bool = False,
        item_other: int | str | None = None,
        item_addr_title: str | None = None,
        item_other_title: str | None = None,
        is_standard: bool = True,
        warning_banner_text: str | None = None,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__VERIFY) if verify else _(i18n_keys.BUTTON__SIGN),
            _(i18n_keys.BUTTON__CANCEL),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.long_message = False
        self.full_message = message
        if len(message) > 150:
            self.message = message[:147] + "..."
            self.long_message = True
        else:
            self.message = message
        if not is_standard:
            self.warning_banner = Banner(
                self.content_area,
                BannerType.Warning,
                warning_banner_text
                or _(i18n_keys.CONTENT__NON_STANDARD_MESSAGE_SIGNATURE),
            )
            self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.item_message = CardItem(
            self.content_area,
            _(i18n_keys.LIST_KEY__MESSAGE__COLON),
            self.message,
            theme_path_png("group-icon-data"),
        )
        self.item_message.align_to(
            self.title if is_standard else self.warning_banner,
            lv.ALIGN.OUT_BOTTOM_MID,  # CENTER
            0,
            40 if is_standard else 8,
        )
        if self.long_message:
            self.show_full_message = NormalButton(
                self.item_message.content, _(i18n_keys.BUTTON__VIEW_DATA)
            )
            self.show_full_message.set_size(lv.SIZE.CONTENT, 77)
            self.show_full_message.add_style(
                StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
            )
            self.show_full_message.align(lv.ALIGN.CENTER, 0, 0)
            self.show_full_message.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
            self.show_full_message.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        self.container = ContainerFlexCol(
            self.content_area, self.item_message, pos=(0, 8), padding_row=0
        )
        # self.container.add_dummy()
        if item_other:
            self.item_other = DisplayItem(
                self.container,
                item_other_title or _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                str(item_other),
            )
        self.item_addr = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__ADDRESS__COLON)
            if not item_addr_title
            else item_addr_title,
            address,
        )
        self.item_addr.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP).radius(10).border_opa(lv.OPA.TRANSP),
            0,
        )
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(665, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

        # self.container.add_dummy()

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_message:
                PageAbleMessage(
                    _(i18n_keys.TITLE__MESSAGE),
                    self.full_message,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TransactionOverview(FullSizeWindow):
    def __init__(
        self,
        title,
        primary_color,
        icon_path,
        sub_icon_path,
        card_title: str,
        card_icon: str,
        items: tuple[tuple[str, str], ...],
        banner_text: str | None = None,
        banner_level: BannerType = BannerType.Warning,
        has_details=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            anim_dir=0,
            primary_color=primary_color,
            icon_path=icon_path,
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        if banner_text:
            self.banner = Banner(
                self.content_area,
                banner_level,
                banner_text,
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
        self.card_group = CardGroup(
            self.content_area,
            self.title if not banner_text else self.banner,
            card_title,
            card_icon,
            items,
            relative_pos=(0, 40 if not banner_text else 16),
            no_align=False,
        )

        if has_details:
            from .components.composite import ShowMore

            self.show_more = ShowMore(self.content_area, self.card_group.pannel)

            self.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(665, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_more.view_btn:
                self.destroy(400)
                self.channel.publish(2)


class TransactionOverviewSend(TransactionOverview):
    def __init__(
        self,
        title,
        primary_color,
        icon_path,
        address,
        has_details=False,
    ):
        super().__init__(
            title,
            primary_color,
            theme_path("send.png"),
            icon_path or theme_path_default("chain_evm_eth-40.png"),
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
            items=((_(i18n_keys.LIST_KEY__TO__COLON), address),),
            has_details=has_details,
        )


class TransactionOverviewNew(FullSizeWindow):
    def __init__(
        self,
        title: str,
        primary_color,
        icon_path: str,
        has_details=None,
        banner_key=None,
        banner_level: BannerType = BannerType.Warning,
        **overview_kwargs,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=icon_path,  # theme_path("send.png"),
            # sub_icon_path=icon_path,
            button_layout=1,
        )

        from .components.signatureinfo import OverviewComponent
        from .components.banner import Banner

        if banner_key:
            self.banner = Banner(
                self.content_area,
                level=banner_level,
                text=banner_key,
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )
        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )

        self.overview = OverviewComponent(
            self.container, **self._filter_overview_params(overview_kwargs)
        )

        if has_details:
            self.view_btn = NormalButton(
                self.content_area,
                f"{LV_SYMBOLS.LV_SYMBOL_ANGLE_DOUBLE_DOWN}  {_(i18n_keys.BUTTON__DETAILS)}",
            )
            self.view_btn.set_size(450, 82)
            self.view_btn.enable()
            self.view_btn.add_style(
                StyleWrapper()
                .bg_color(lv_theme.BTN_CANCEL_BG)
                .text_color(lv_theme.DT_TIP_FG)
                .text_font(font_GeistSemiBold26),
                0,
            )
            self.view_btn.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)
            self.view_btn.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        # self.update_btn_layout()

    def _filter_overview_params(self, kwargs: dict) -> dict:
        supported_params = {
            "title",
            "icon",
            "to_address",
            "approve_spender",
            "max_fee",
            "token_address",
        }

        return {
            key: value
            for key, value in kwargs.items()
            if key in supported_params and value is not None
        }

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.view_btn:
                self.destroy(400)
                self.channel.publish(2)


class TransactionDetailsETH(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        contract_addr=None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        sub_icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.group_directions.add_style(StyleWrapper().radius(15), 0)
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.group_fees.add_style(StyleWrapper().radius(15), 0)
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if not is_eip1559:
            if gas_price:
                self.item_group_body_gas_price = DisplayItem(
                    self.group_fees,
                    _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
                    gas_price,
                )
        else:
            self.item_group_body_priority_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                max_priority_fee_per_gas,
            )
            self.item_group_body_max_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON),
                max_fee_per_gas,
            )
        if total_amount is None:
            if not contract_addr:  # token transfer
                total_amount = f"{amount}\n{fee_max}"
            else:  # nft transfer
                total_amount = f"{fee_max}"
        self.item_group_body_total_amount = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
            total_amount,
        )
        # # self.group_fees.add_dummy()

        if contract_addr or evm_chain_id:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if evm_chain_id:
                self.item_group_body_chain_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                    str(evm_chain_id),
                )
            if contract_addr:
                self.item_group_body_contract_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CONTRACT_ADDRESS__COLON),
                    contract_addr,
                )
                self.item_group_body_token_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__TOKEN_ID__COLON),
                    token_id,
                )
            # # self.group_more.add_dummy()

        if raw_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(raw_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str
            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON),
                self.data,
                theme_path_png("group-icon-data"),
            )
            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TransactionDetailsBase(FullSizeWindow):
    ALLOWED_SECTIONS = ["amount", "direction", "fee", "more", "data"]

    def __init__(
        self,
        title,
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path: str | None = None,
        sub_icon_path: str | None = None,
        banner_text: str | None = None,
        banner_level: BannerType = BannerType.Warning,
        section_order: list[str] = None,
        **kwargs,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            sub_icon_path=sub_icon_path,
        )
        self.primary_color = primary_color

        if any(
            section_name.split("_")[0] not in TransactionDetailsBase.ALLOWED_SECTIONS
            for section_name in kwargs.keys()
        ):
            raise ValueError("Invalid section name")
        if banner_text:
            self.banner = Banner(
                self.content_area,
                banner_level,
                banner_text,
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
        self.container = ContainerFlexCol(
            self.content_area,
            self.title if not banner_text else self.banner,
            pos=(0, 40 if not banner_text else 16),
        )
        self.section_order = section_order or TransactionDetailsBase.ALLOWED_SECTIONS
        for section_prefix in self.section_order:
            section_name = f"{section_prefix}_section"
            section_params = kwargs.get(section_name, None)
            if section_params is None:
                continue
            if section_prefix == "amount":
                assert isinstance(
                    section_params, tuple
                ), "amount section params must be a tuple"
                self.group_amounts = AmountGroup(
                    self.container,
                    section_params,
                )
            elif section_prefix == "direction":
                assert isinstance(
                    section_params, tuple
                ), "direction section params must be a tuple"
                self.group_directions = DirectionGroup(
                    self.container,
                    section_params,
                )
            elif section_prefix == "fee":
                assert isinstance(
                    section_params, tuple
                ), "fee section params must be a tuple"
                self.group_fees = FeeGroup(
                    self.container,
                    section_params,
                )
            elif section_prefix == "more":
                assert isinstance(
                    section_params, tuple
                ), "more section params must be a tuple"
                self.group_more = MoreGroup(
                    self.container,
                    section_params,
                )
            elif section_prefix == "data":
                assert isinstance(
                    section_params, dict
                ), "data section params must be a dict"
                self.group_data = RawDataItem(
                    self.container,
                    section_params.get("raw_data", None),
                    max_length=section_params.get("max_length", 225),
                    primary_color=self.primary_color,
                )


class TransactionDetailsEIP7702(TransactionDetailsBase):
    def __init__(
        self,
        title: str,
        authorty_addr: str,
        delegate_addr: str | None,
        value: str,
        nonce: str,
        network: str,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        fee_max: str = None,
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path: str | None = None,
    ):

        super().__init__(
            title,
            primary_color,
            icon_path,
            direction_section=(
                (_(i18n_keys.FIELDS_ACCOUNT), authorty_addr),
                (_(i18n_keys.FIELDS_DELEGATE_TO), delegate_addr),
            ),
            more_section=(
                (_(i18n_keys.LIST_KEY__AMOUNT__COLON), value),
                ("Nonce", nonce),
                (
                    _(i18n_keys.FIELDS_DELEGATE_ON_NETWORK)
                    if delegate_addr
                    else _(i18n_keys.FIELDS_REVOKE_ON_NETWORK),
                    network,
                ),
            ),
            fee_section=(
                (_(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON), fee_max),
                (
                    _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                    max_priority_fee_per_gas,
                ),
                (_(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON), max_fee_per_gas),
            ),
            section_order=["direction", "more", "fee"],
        )


class SafeTxSafeApproveHash(FullSizeWindow):
    def __init__(
        self,
        title: str,
        address_from: str,
        address_to: str,
        hash_to_approve: str,
        nonce_from: str,
        fee_max: str,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path: str | None = None,
        chain_id: int | None = None,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if not is_eip1559:
            if gas_price:
                self.item_group_body_gas_price = DisplayItem(
                    self.group_fees,
                    _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
                    gas_price,
                )
        else:
            self.item_group_body_priority_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                max_priority_fee_per_gas,
            )
            self.item_group_body_max_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON),
                max_fee_per_gas,
            )
        # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_hash_to_approve = DisplayItem(
            self.group_more,
            "SafeTxHash",
            hash_to_approve,
        )
        self.item_group_body_nonce_from = DisplayItem(
            self.group_more,
            "Nonce",
            nonce_from,
        )
        if chain_id:
            self.item_group_body_chain_id = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                str(chain_id),
            )
        # self.group_more.add_dummy()


class SafeTxExecTransaction(FullSizeWindow):
    def __init__(
        self,
        from_address: str,
        to_address: str,
        to_address_safe: str,
        value_safe: str,
        operation: int,
        safe_tx_gas: str,
        base_gas: str,
        gas_price_safe: str,
        gas_token: str,
        refund_receiver: str,
        signatures: str,
        fee_max: str,
        nonce: int,
        is_eip1559: bool = True,
        chain_id: int | None = None,
        call_data: str | dict[str, str] | None = None,
        call_method: str | None = None,
        gas_price: str | None = None,
        max_priority_fee_per_gas: str | None = None,
        max_fee_per_gas: str | None = None,
        icon_path: str | None = None,
        primary_color=lv_theme.APP_CORRECT_BG,
    ):
        self.primary_color = primary_color
        super().__init__(
            _(i18n_keys.GNOSIS_SAFE_SIG_TITLE),
            None,
            _(i18n_keys.BUTTON__CONFIRM),
            _(i18n_keys.BUTTON__REJECT),
            icon_path=icon_path,
            primary_color=primary_color,
            button_layout=1,
        )
        from .components.listitem import RawDataOverviewWithTitle

        is_delegate_call = operation == 1
        if is_delegate_call:
            self.warning_banner = Banner(
                self.content_area,
                BannerType.Danger,
                _(i18n_keys.GNOSIS_SAFE_SIG_DELEGATECALL_WARNING_TEXT),
            )
            self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(
            self.content_area,
            self.title if not is_delegate_call else self.warning_banner,
            pos=(0, 40 if not is_delegate_call else 8),
        )
        self.group_safe_tx = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_safe_tx,
            "execTransaction",
            theme_path_png("group-icon-more"),
        )
        self.group_body_to_addr = DisplayItem(
            self.group_safe_tx,
            "To",
            to_address_safe,
        )
        self.item_group_body_value_safe = DisplayItem(
            self.group_safe_tx,
            "Value",
            value_safe,
        )
        self.item_group_body_operation = DisplayItem(
            self.group_safe_tx,
            "Operation",
            "0 (CALL)" if operation == 0 else "#FF1100 1 (DELEGATECALL)#",
        )
        if call_method and isinstance(call_data, dict):
            from .components.listitem import DisplayItemWithFlexColPanel

            self.item_group_body_call_args = DisplayItemWithFlexColPanel(
                self.group_safe_tx,
                "Data",
            )
            item_group_body_call_args_panel = (
                self.item_group_body_call_args.flex_col_panel
            )
            self.item_group_body_call_args_method = DisplayItem(
                item_group_body_call_args_panel,
                None,
                call_method,
                bg_color=lv_theme.CONT_ITEM_SUB_BG,
                padding_hor=12,
            )
            for key, value in call_data.items():
                self.item_group_body_call_args_value = DisplayItem(
                    item_group_body_call_args_panel,
                    key,
                    value,
                    bg_color=lv_theme.CONT_ITEM_SUB_BG,
                    padding_hor=12,
                )
        elif call_data and isinstance(call_data, str):
            self.item_group_body_call_data = RawDataOverviewWithTitle(
                self.group_safe_tx,
                "Data",
                call_data,
                brief_tip=_(i18n_keys.BUTTON__VIEW_DATA),
                primary_color=self.primary_color,
            )
        self.item_group_body_safe_tx_gas = DisplayItem(
            self.group_safe_tx,
            "SafeTxGas",
            str(safe_tx_gas),
        )
        self.item_group_body_base_gas = DisplayItem(
            self.group_safe_tx,
            "BaseGas",
            str(base_gas),
        )
        self.item_group_body_gas_price_safe = DisplayItem(
            self.group_safe_tx,
            "GasPrice",
            gas_price_safe,
        )
        self.item_group_body_gas_token = DisplayItem(
            self.group_safe_tx,
            "GasToken",
            gas_token,
        )
        self.item_group_body_refund_receiver = DisplayItem(
            self.group_safe_tx,
            "RefundReceiver",
            refund_receiver,
        )
        self.item_group_body_signatures = RawDataOverviewWithTitle(
            self.group_safe_tx,
            "Signatures",
            signatures,
            brief_tip=_(i18n_keys.BUTTON__VIEW_DATA),
            primary_color=self.primary_color,
        )
        # self.group_safe_tx.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            to_address,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            from_address,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )

        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if not is_eip1559:
            if gas_price:
                self.item_group_body_gas_price = DisplayItem(
                    self.group_fees,
                    _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
                    gas_price,
                )
        else:
            self.item_group_body_priority_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                max_priority_fee_per_gas,
            )
            self.item_group_body_max_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON),
                max_fee_per_gas,
            )
        # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_nonce_safe = DisplayItem(
            self.group_more,
            "Nonce",
            str(nonce),
        )
        if chain_id:
            self.item_group_body_chain_id = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                str(chain_id),
            )
        # self.group_more.add_dummy()


class TransactionDetailsETHNew(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        contract_addr=None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        sub_icon_path=None,
        striped=False,
        token_address=None,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        from .components.signatureinfo import (
            AmountComponent,
            DirectionComponent,
            FeeComponent,
            MoreInfoComponent,
            DataComponent,
        )

        # 1. Amount Component(optional)
        if striped and amount:
            self.amount_component = AmountComponent(self.container, amount=amount)

        # 2. Direction Component
        self.direction_component = DirectionComponent(
            self.container, to_address=address_to, from_address=address_from
        )

        # 3. Fee Component
        fee_params = {
            "maximum_fee": fee_max,
        }

        if is_eip1559:
            if max_priority_fee_per_gas:
                fee_params["priority_fee_per_gas"] = max_priority_fee_per_gas
            if max_fee_per_gas:
                fee_params["max_fee_per_gas"] = max_fee_per_gas
        else:
            if gas_price:
                fee_params["gas_price"] = gas_price

        self.fee_component = FeeComponent(self.container, **fee_params)

        # 4. More Info Component(optional)
        more_info_params = {}
        if evm_chain_id:
            more_info_params["chain_id"] = evm_chain_id
        if contract_addr:
            more_info_params["contract_address"] = contract_addr
        if token_id:
            more_info_params["token_id"] = token_id
        if token_address:
            more_info_params["token_address"] = token_address

        if more_info_params:
            self.more_info_component = MoreInfoComponent(
                self.container, **more_info_params
            )

        # 5. Data Component(optional)
        if raw_data:
            from trezor import strings

            data_str = strings.format_customer_data(raw_data)
            if data_str:
                self.data_component = DataComponent(
                    self.container,
                    data=data_str,
                    max_length=225,
                    primary_color=self.primary_color,
                )
        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ApproveErc20ETHOverview(FullSizeWindow):
    def __init__(
        self,
        title,
        approve_spender,
        max_fee,
        token_address,
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path=theme_path("send.png"),
        sub_icon_path=None,
        has_details=None,
        is_unlimited=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.title.set_style_text_font(font_GeistSemiBold48, 0)
        self.primary_color = primary_color

        from .components.signatureinfo import OverviewComponent
        from .components.banner import Banner

        if is_unlimited:
            self.banner = Banner(
                self.content_area,
                level=BannerType.Warning,
                text=_(i18n_keys.APPROVE_UNLIMITED_WARNING),
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )
        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )
        self.overview = OverviewComponent(
            self.container,
            approve_spender=approve_spender,
            max_fee=max_fee,
            token_address=token_address,
        )
        if has_details:
            self.view_btn = NormalButton(
                self.content_area,
                f"{LV_SYMBOLS.LV_SYMBOL_ANGLE_DOUBLE_DOWN}  {_(i18n_keys.BUTTON__DETAILS)}",
            )
            self.view_btn.set_size(450, 82)
            self.view_btn.add_style(StyleWrapper().text_font(font_GeistSemiBold26), 0)
            self.view_btn.enable()
            self.view_btn.align_to(self.overview.group, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)
            self.view_btn.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.update_btn_layout()
        # self.content_area.set_style_min_height(650, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.view_btn:
                self.destroy(400)
                self.channel.publish(2)


class ApproveErc20ETH(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        token_address: str | None = None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        icon_path=theme_path("send.png"),
        sub_icon_path=None,
        striped=False,
        is_unlimited=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.title.set_style_text_font(font_GeistSemiBold48, 0)
        self.primary_color = primary_color

        from .components.signatureinfo import (
            AmountComponent,
            DirectionComponent,
            FeeComponent,
            MoreInfoComponent,
        )
        from .components.banner import Banner

        if is_unlimited:
            self.banner = Banner(
                self.content_area,
                level=BannerType.Warning,
                text=_(i18n_keys.APPROVE_UNLIMITED_WARNING),
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )

        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )

        if striped and amount:
            self.amount_component = AmountComponent(self.container, amount=amount)

        self.direction = DirectionComponent(
            self.container,
            approve_spender=address_to,
            from_address=address_from,
        )

        self.fee = FeeComponent(
            self.container,
            maximum_fee=fee_max,
            gas_price=gas_price if not is_eip1559 else None,
            priority_fee_per_gas=max_priority_fee_per_gas if is_eip1559 else None,
            max_fee_per_gas=max_fee_per_gas if is_eip1559 else None,
        )

        self.more = MoreInfoComponent(
            self.container,
            token_address=token_address,
            chain_id=evm_chain_id,
        )

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()


class TransactionTronNew(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        banner_key,
        banner_level,
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path=theme_path("send.png"),
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        if banner_key:
            self.banner = Banner(
                self.content_area,
                level=banner_level,
                text=banner_key,
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )
        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )

        from .components.signatureinfo import DirectionComponent

        self.direction = DirectionComponent(
            self.container,
            to_address=address_to,
            from_address=address_from,
        )
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(250, 0)
        # self.content_area.set_style_max_height(250, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class TransactionDetailsBenFen(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        contract_addr=None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        sub_icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if not is_eip1559:
            if gas_price:
                self.item_group_body_gas_price = DisplayItem(
                    self.group_fees,
                    _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
                    gas_price,
                )
        else:
            self.item_group_body_priority_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                max_priority_fee_per_gas,
            )
            self.item_group_body_max_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON),
                max_fee_per_gas,
            )
        if amount != "All":
            if total_amount is None:
                if not contract_addr:
                    total_amount = f"{amount}\n{fee_max}"
                else:
                    total_amount = f"{fee_max}"
            self.item_group_body_total_amount = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
                total_amount,
            )

        # self.group_fees.add_dummy()

        if contract_addr or evm_chain_id:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if evm_chain_id:
                self.item_group_body_chain_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                    str(evm_chain_id),
                )
            if contract_addr:
                self.item_group_body_contract_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CONTRACT_ADDRESS__COLON),
                    contract_addr,
                )
                self.item_group_body_token_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__TOKEN_ID__COLON),
                    token_id,
                )
            # self.group_more.add_dummy()

        if raw_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(raw_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str
            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON),
                self.data,
                theme_path_png("group-icon-data"),
            )
            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TransactionDetailsAlepHium(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        subtitle=None,
        amount=None,
        gas_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        token_id=None,
        raw_data=None,
        icon_path=None,
        sub_icon_path=None,
        token_amount=None,
    ):
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        if raw_data:
            self.container = ContainerFlexCol(
                self.content_area, self.subtitle, pos=(0, 40)
            )
        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )
        if amount:
            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.FORM__DIRECTIONS),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_to_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__TO__COLON),
                address_to,
            )
            self.item_group_body_from_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__FROM__COLON),
                address_from,
            )
            # self.group_directions.add_dummy()

        if token_amount:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.SUBTITLE__ADA_TX_CONTAINS_TOKEN),
                theme_path_default("tools_notice.png"),
            )
            # self.group_amounts.add_dummy()
            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_to_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__TOKEN_ID__COLON),
                token_id,
            )
            self.item_group_body_from_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                str(token_amount),
            )
            # self.group_directions.add_dummy()

            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.FORM__DIRECTIONS),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_to_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__TO__COLON),
                address_to,
            )
            self.item_group_body_from_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__FROM__COLON),
                address_from,
            )
            # self.group_directions.add_dummy()

        if gas_amount:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_gas_price = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__TRANSACTION_FEE__COLON),
                gas_amount,
            )

        if raw_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(raw_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str

            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON),
                self.data,
                theme_path_png("group-icon-data"),
            )

            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.update_btn_layout()
        # self.content_area.set_style_min_height(650, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class ContractDataOverview(FullSizeWindow):
    def __init__(self, title, description, data, primary_color):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            anim_dir=0,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_size = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__SIZE__COLON), description
        )
        # self.container.add_dummy()

        self.data_str = data
        self.long_data = False
        if len(self.data_str) > 225:
            self.long_data = True
            self.data = self.data_str[:222] + "..."
        else:
            self.data = self.data_str
        self.item_data = CardItem(
            self.content_area,
            _(i18n_keys.LIST_KEY__DATA__COLON),
            self.data,
            theme_path_png("group-icon-data"),
        )
        self.item_data.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)
        if self.long_data:
            self.show_full_data = NormalButton(
                self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
            )
            self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
            self.show_full_data.add_style(
                StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
            )
            self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
            self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
            self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                    page_size=351,
                )


class BlobDisPlay(FullSizeWindow):
    def __init__(
        self,
        title,
        description: str,
        content: str,
        icon_path: str = theme_path_png("triangle-warning"),
        anim_dir: int = 1,
        primary_color=lv_theme.APP_CORRECT_BG,
        subtitle: str | None = None,
        item_key: str | None = None,
        item_value: str | None = None,
    ):
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            icon_path=icon_path,
            anim_dir=anim_dir,
            primary_color=primary_color or lv_theme.APP_CORRECT_BG,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(
            self.content_area,
            self.subtitle if subtitle else self.title,
            pos=(0, 40),
            padding_row=0,
        )
        # self.container.add_dummy()
        if item_key and item_value:
            self.item_key_value = DisplayItem(self.container, item_key, item_value)
        self.item_data = DisplayItem(self.container, description, content[:240])
        # self.container.add_dummy()
        self.long_message = False
        if len(content) > 240:
            self.long_message = True
            self.btn_yes.label.set_text(_(i18n_keys.BUTTON__VIEW))
            self.data = content

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.btn_yes:
                if self.long_message:
                    PageAbleMessage(
                        _(i18n_keys.TITLE__MESSAGE),
                        self.data,
                        self.channel,
                        primary_color=self.primary_color,
                    )
                    self.destroy()
                else:
                    self.show_unload_anim()
                    self.channel.publish(1)
            elif target == self.btn_no:
                self.show_dismiss_anim()
                self.channel.publish(0)
            elif target in (self.nav_back, self.nav_back.nav_btn):
                self.show_dismiss_anim()
                self.channel.publish(0)


class ConfirmMetaData(FullSizeWindow):
    def __init__(self, title, subtitle, description, data, primary_color, icon_path):
        if __debug__:
            self.layout_data = data

        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )

        if description:
            self.container = ContainerFlexCol(
                self.content_area, self.subtitle, pos=(0, 40), padding_row=0
            )
            # self.container.add_dummy()
            self.item1 = DisplayItem(self.container, description, data)
            # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    if __debug__:

        def read_content(self) -> list[str]:
            return (
                [self.layout_title or ""]
                + [self.layout_subtitle or ""]
                + [self.layout_data or ""]
            )


class TransactionDetailsBTC(FullSizeWindow):
    def __init__(
        self,
        title: str,
        amount: str,
        fee: str,
        total: str,
        primary_color,
        icon_path: str,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            anim_dir=0,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=8
        )
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()
        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__FEE__COLON),
            fee,
        )
        self.item_group_body_total_amount = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
            total,
        )
        # self.group_fees.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class JointTransactionDetailsBTC(FullSizeWindow):
    def __init__(self, title: str, amount: str, total: str, primary_color):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_spend = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__AMOUNT_YOU_SPEND__COLON), amount
        )
        self.item_total = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON), total
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ModifyFee(FullSizeWindow):
    def __init__(self, description: str, fee_change: str, fee_new: str, primary_color):
        super().__init__(
            _(i18n_keys.TITLE__MODIFY_FEE),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_fee_change = DisplayItem(self.container, description, fee_change)
        self.item_fee_new = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__NEW_FEE__COLON), fee_new
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ModifyOutput(FullSizeWindow):
    def __init__(
        self,
        address: str,
        description: str,
        amount_change: str,
        amount_new: str,
        primary_Color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__MODIFY_AMOUNT),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_Color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_addr = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__ADDRESS__COLON), address
        )
        self.item_amount_change = DisplayItem(
            self.container, description, amount_change
        )
        self.item_amount_new = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__NEW_AMOUNT__COLON), amount_new
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmReplacement(FullSizeWindow):
    def __init__(self, title: str, txids: list[str], primary_color):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        for txid in txids:
            self.item_body_tx_id = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__TRANSACTION_ID__COLON),
                txid,
            )
        # self.group_directions.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmPaymentRequest(FullSizeWindow):
    def __init__(self, title: str, subtitle, amount: str, to_addr: str, primary_color):
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_to_addr = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__TO__COLON), to_addr
        )
        self.item_amount = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__AMOUNT__COLON), amount
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmDecredSstxSubmission(FullSizeWindow):
    def __init__(
        self, title: str, subtitle: str, amount: str, to_addr: str, primary_color
    ):
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_amount = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__AMOUNT__COLON), amount
        )
        self.item_to_addr = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__TO__COLON), to_addr
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmCoinJoin(FullSizeWindow):
    def __init__(
        self,
        title: str,
        coin_name: str,
        max_rounds: str,
        max_fee_per_vbyte: str,
        primary_color,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_coin_name = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__COIN_NAME__COLON), coin_name
        )
        self.item_mrc = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__MAXIMUM_ROUNDS__COLON), max_rounds
        )
        self.item_fee_rate = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__MAXIMUM_MINING_FEE__COLON),
            max_fee_per_vbyte,
        )
        # self.container.add_dummy()

        self.content_area.add_style(
            StyleWrapper().bg_color(lv_theme.TEST_FG).bg_opa(lv.OPA.COVER),
            0,
        )
        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmSignIdentity(FullSizeWindow):
    def __init__(self, title: str, identity: str, subtitle: str | None, primary_color):
        super().__init__(
            title,
            subtitle,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        align_base = self.title if subtitle is None else self.subtitle
        self.container = ContainerFlexCol(
            self.content_area, align_base, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_id = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__IDENTITY__COLON), identity
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmProperties(FullSizeWindow):
    def __init__(self, title: str, properties: list[tuple[str, str]], primary_color):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        for key, value in properties:
            self.item = DisplayItem(self.container, f"{key.upper()}", value)
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ConfirmTransferBinance(FullSizeWindow):
    def __init__(self, items: list[tuple[str, str, str]], primary_color, icon_path):
        super().__init__(
            _(i18n_keys.TITLE__CONFIRM_TRANSFER),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        for key, value, address in items:
            self.item_key = DisplayItem(self.container, key, "")
            self.item_amount = DisplayItem(
                self.container, _(i18n_keys.LIST_KEY__AMOUNT__COLON), value
            )
            self.item_to_addr = DisplayItem(
                self.container, _(i18n_keys.LIST_KEY__TO__COLON), address
            )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class ShouldShowMore(FullSizeWindow):
    def __init__(
        self, title: str, key: str, value: str, button_text: str, primary_color
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item = DisplayItem(self.container, f"{key}:", value)
        # self.container.add_dummy()
        self.show_more = NormalButton(self.content_area, button_text)
        self.show_more.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 32)
        self.show_more.add_event_cb(self.on_show_more, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_show_more(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_more:
                # 2 means show more
                self.channel.publish(2)
                self.destroy()


class EIP712DOMAIN(FullSizeWindow):
    def __init__(self, title: str, primary_color, icon_path, **kwargs):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        if kwargs.get("name"):
            self.item_name = DisplayItem(
                self.container, "name (string):", kwargs.get("name")
            )
        if kwargs.get("version"):
            self.item_version = DisplayItem(
                self.container, "version (string):", kwargs.get("version")
            )
        if kwargs.get("chainId"):
            self.item_chain_id = DisplayItem(
                self.container, "chainId (uint256):", kwargs.get("chainId")
            )
        if kwargs.get("verifyingContract"):
            self.item_vfc = DisplayItem(
                self.container,
                "verifyingContract (address):",
                kwargs.get("verifyingContract"),
            )
        if kwargs.get("salt"):
            self.item_salt = DisplayItem(
                self.container, "salt (bytes32):", kwargs.get("salt")
            )
        # self.container.add_dummy()
        # self.update_btn_layout()
        # self.content_area.set_style_min_height(650, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class EIP712Warning(FullSizeWindow):
    def __init__(
        self,
        title: str,
        warning_level: BannerType,
        text,
        primary_type,
        primary_color,
        icon_path,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.warning_banner = Banner(self.content_area, warning_level, text)
        self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(
            self.content_area, self.warning_banner, pos=(0, 24), padding_row=0
        )
        # self.container.add_dummy(bg_color=lv_theme.CONT_ITEM_BOARD_BG)
        self.primary_type = DisplayItem(
            self.container,
            "PrimaryType:",
            primary_type,
            bg_color=lv_theme.CONT_ITEM_BG,
        )
        # self.container.add_dummy(bg_color=lv_theme.CONT_ITEM_BOARD_BG)

        # self.update_btn_layout()
        # self.content_area.set_style_min_height(650, 0)
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class TonTransfer(FullSizeWindow):
    def __init__(
        self,
        address_from,
        address_to,
        amount,
        memo,
        primary_color=None,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("TON"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.item1 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__AMOUNT__COLON), amount
        )
        self.item2 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__TO__COLON), address_to
        )
        self.item3 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__FROM__COLON), address_from
        )
        if memo:
            self.item4 = DisplayItem(
                self.container, _(i18n_keys.LIST_KEY__MEMO__COLON), memo
            )


class TonTransaction(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        contract_addr=None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        sub_icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if not is_eip1559:
            if gas_price:
                self.item_group_body_gas_price = DisplayItem(
                    self.group_fees,
                    _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
                    gas_price,
                )
        else:
            self.item_group_body_priority_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__PRIORITY_FEE_PER_GAS__COLON),
                max_priority_fee_per_gas,
            )
            self.item_group_body_max_fee_per_gas = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__MAXIMUM_FEE_PER_GAS__COLON),
                max_fee_per_gas,
            )
        if total_amount is None:
            if not contract_addr:  # token transfer
                total_amount = f"{amount}\n{fee_max}"
            else:  # nft transfer
                total_amount = f"{fee_max}"
        self.item_group_body_total_amount = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
            total_amount,
        )
        # self.group_fees.add_dummy()

        if contract_addr or evm_chain_id:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if evm_chain_id:
                self.item_group_body_chain_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                    str(evm_chain_id),
                )
            if contract_addr:
                self.item_group_body_contract_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CONTRACT_ADDRESS__COLON),
                    contract_addr,
                )
                self.item_group_body_token_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__TOKEN_ID__COLON),
                    token_id,
                )
            # self.group_more.add_dummy()

        if raw_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(raw_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str
            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON),
                self.data,
                theme_path_png("group-icon-data"),
            )
            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TonConnect(FullSizeWindow):
    def __init__(
        self,
        doamin,
        address,
        payload,
        primary_color=None,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_MESSAGE).format("TON"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.item1 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__DOMAIN__COLON), doamin
        )
        self.item2 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__ADDRESS__COLON), address
        )
        # self.item3 = DisplayItem(
        #     self.container, _(i18n_keys.LIST_KEY__FROM__COLON), address_from
        # )
        if payload:
            self.item3 = DisplayItem(
                self.container, _(i18n_keys.LIST_KEY__MEMO__COLON), payload
            )

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class TonMessage(FullSizeWindow):
    def __init__(
        self,
        title,
        address,
        message,
        domain,
        primary_color,
        icon_path,
        verify: bool = False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__VERIFY) if verify else _(i18n_keys.BUTTON__SIGN),
            _(i18n_keys.BUTTON__CANCEL),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.long_message = False
        self.full_message = message
        if len(message) > 150:
            self.message = message[:147] + "..."
            self.long_message = True
        else:
            self.message = message
        self.item_message = CardItem(
            self.content_area,
            _(i18n_keys.LIST_KEY__MESSAGE__COLON),
            self.message,
            theme_path_png("group-icon-data"),
        )
        self.item_message.align_to(self.title, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 40)
        if self.long_message:
            self.show_full_message = NormalButton(
                self.item_message.content, _(i18n_keys.BUTTON__VIEW_DATA)
            )
            self.show_full_message.set_size(185, 77)
            self.show_full_message.add_style(
                StyleWrapper().text_font(font_GeistSemiBold26), 0
            )
            self.show_full_message.align(lv.ALIGN.CENTER, 0, 0)
            self.show_full_message.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
            self.show_full_message.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        self.container = ContainerFlexCol(
            self.content_area, self.item_message, pos=(0, 8), padding_row=0
        )
        # self.container.add_dummy()

        self.item_addr = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__ADDRESS__COLON), address
        )
        self.item_domain = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__DOMAIN__COLON), domain
        )

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_message:
                PageAbleMessage(
                    _(i18n_keys.TITLE__MESSAGE),
                    self.full_message,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TransactionDetailsTON(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        is_eip1559=False,
        gas_price=None,
        max_priority_fee_per_gas=None,
        max_fee_per_gas=None,
        total_amount=None,
        primary_color=lv_theme.APP_CORRECT_BG,
        contract_addr=None,
        token_id=None,
        evm_chain_id=None,
        raw_data=None,
        is_raw_data=False,
        sub_icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=sub_icon_path,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        if contract_addr or evm_chain_id:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if evm_chain_id:
                self.item_group_body_chain_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
                    str(evm_chain_id),
                )
            if contract_addr:
                self.item_group_body_contract_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CONTRACT_ADDRESS__COLON),
                    contract_addr,
                )
                self.item_group_body_token_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__TOKEN_ID__COLON),
                    token_id,
                )
            # self.group_more.add_dummy()

        if raw_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(raw_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str
            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON)
                if self.data.startswith("b5ee9c72")
                else _(i18n_keys.LIST_KEY__MEMO__COLON),
                self.data,
                theme_path_png("group-icon-data")
                if self.data.startswith("b5ee9c72")
                else theme_path_png("group-icon-more"),
            )

            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class TransactionDetailsTRON(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        primary_color,
        icon_path,
        total_amount=None,
        striped=False,
        banner_key=None,
        banner_level=BannerType.Default,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )

        if banner_key:
            self.banner = Banner(
                self.content_area,
                level=banner_level,
                text=banner_key,
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )
        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )

        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_max = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if total_amount is None:
            total_amount = f"{amount}\n{fee_max}"
        self.item_group_body_total = DisplayItem(
            self.group_fees, _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON), total_amount
        )
        # self.group_fees.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class TransactionDetailsNear(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class SecurityCheck(FullSizeWindow):
    def __init__(self):
        super().__init__(
            title=_(i18n_keys.TITLE__SECURITY_CHECK),
            subtitle=_(i18n_keys.SUBTITLE__SECURITY_CHECK),
            confirm_text=_(i18n_keys.BUTTON__CONFIRM),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            icon_path=theme_path_png("security-check"),
            anim_dir=2,
            button_layout=1,
        )
        self.subtitle.add_style(
            StyleWrapper().text_align_left(),
            0,
        )


class PassphraseDisplayConfirm(FullSizeWindow):
    def __init__(self, passphrase: str, from_device: bool):
        super().__init__(
            title=_(i18n_keys.TITLE__USE_THIS_PASSPHRASE),
            subtitle=_(i18n_keys.SUBTITLE__USE_THIS_PASSPHRASE),
            confirm_text=_(i18n_keys.BUTTON__CONFIRM),
            cancel_text=_(i18n_keys.GLOBAL__EDIT)
            if from_device
            else _(i18n_keys.BUTTON__CANCEL),
            anim_dir=0,
            button_layout=1,
        )

        # self.warning_banner = Banner(
        #     self.content_area, 2, _(i18n_keys.PASSPHRASE_FORGETTING_WARNING_TEXT)
        # )
        # self.warning_banner.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
        self.subtitle.add_style(
            StyleWrapper().text_color(lv_theme.APP_ERROR_FG),
            0,
        )
        self.panel = lv.obj(self.content_area)
        self.panel.remove_style_all()
        self.panel.set_size(450, 210)
        self.panel.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)

        self.panel.add_style(
            StyleWrapper()
            .bg_color(lv_theme.CONT_ITEM_BG)
            .bg_opa()
            .border_width(0)
            .text_font(font_GeistSemiBold38)
            .text_color(lv_theme.CONT_ITEM_FG)
            .text_align_left()
            .pad_ver(16)
            .pad_hor(24)
            .radius(40),
            0,
        )
        self.content = lv.label(self.panel)
        self.content.set_size(lv.pct(100), lv.pct(100))
        self.content.set_text(passphrase)
        self.content.set_long_mode(lv.label.LONG.WRAP)

        self.input_count_tips = lv.obj(self.content_area)
        self.input_count_tips.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
        self.input_count_tips.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP).border_width(0),
            0,
        )
        self.input_count_tips1 = lv.label(self.input_count_tips)
        self.input_count_tips1.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_letter_space(1)
            .text_color(lv_theme.INPUT_FG),
            0,
        )
        self.input_count_tips.add_flag(lv.obj.FLAG.HIDDEN)
        self.input_count_tips2 = lv.label(self.input_count_tips)
        self.input_count_tips2.align(lv.ALIGN.OUT_RIGHT_MID, 0, 0)
        self.input_count_tips2.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_letter_space(1)
            .text_color(lv_theme.INPUT_TIP_FG),
            0,
        )
        self.input_count_tips1.set_text(f"{len(passphrase)}/")
        self.input_count_tips2.set_text("50")
        self.input_count_tips2.align_to(
            self.input_count_tips1, lv.ALIGN.OUT_RIGHT_MID, 0, 0
        )
        self.input_count_tips.align_to(self.panel, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

    def show_unload_anim(self):
        self.clean()
        self.destroy(200)


class SolBlindingSign(FullSizeWindow):
    def __init__(self, fee_payer: str, message_hex: str, primary_color, icon_path):
        super().__init__(
            _(i18n_keys.TITLE__VIEW_TRANSACTION),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.warning_banner = Banner(
            self.content_area,
            BannerType.Warning,
            _(i18n_keys.TITLE__UNKNOWN_TRANSACTION),
        )
        self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(self.content_area, self.title)
        self.container.align_to(self.warning_banner, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_fee_payer = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FEE_PAYER__COLON),
            fee_payer,
        )
        # self.group_directions.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_format = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__FORMAT__COLON),
            _(i18n_keys.LIST_VALUE__UNKNOWN__COLON),
        )
        self.item_group_body_message_hex = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__MESSAGE_HASH__COLON),
            message_hex,
        )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class SolTransfer(FullSizeWindow):
    def __init__(
        self,
        title,
        from_addr: str,
        fee_payer: str,
        to_addr: str,
        amount: str,
        primary_color,
        icon_path,
        striped: bool = False,
    ):
        super().__init__(
            title=title,
            subtitle=None,
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            cancel_text=_(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            to_addr,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions, _(i18n_keys.LIST_KEY__FROM__COLON), from_addr
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_payer = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__FEE_PAYER__COLON),
            fee_payer,
        )
        # self.group_fees.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class SolCreateAssociatedTokenAccount(FullSizeWindow):
    def __init__(
        self,
        fee_payer: str,
        funding_account: str,
        associated_token_account: str,
        wallet_address: str,
        token_mint: str,
        primary_color,
    ):
        super().__init__(
            title=_(i18n_keys.TITLE__CREATE_TOKEN_ACCOUNT),
            subtitle=None,
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            cancel_text=_(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_body_ata = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__NEW_TOKEN_ACCOUNT),
            associated_token_account,
        )
        self.item_body_owner = DisplayItem(
            self.group_directions, _(i18n_keys.LIST_KEY__OWNER), wallet_address
        )
        self.item_body_mint_addr = DisplayItem(
            self.group_directions, _(i18n_keys.LIST_KEY__MINT_ADDRESS), token_mint
        )
        self.item_body_founder = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FUNDED_BY__COLON),
            funding_account,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_payer = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__FEE_PAYER__COLON),
            fee_payer,
        )
        # self.group_fees.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class SolTokenTransfer(FullSizeWindow):
    def __init__(
        self,
        title,
        from_addr: str,
        to: str,
        amount: str,
        source_owner: str,
        fee_payer: str,
        primary_color,
        icon_path,
        token_mint: str | None = None,
        striped: bool = False,
    ):
        super().__init__(
            title,
            subtitle=None,
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            cancel_text=_(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )

        if token_mint:
            self.banner = Banner(
                self.content_area,
                level=BannerType.Warning,
                text=_(i18n_keys.WARNING_UNRECOGNIZED_TOKEN),
            )
            self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 30)
            self.container = ContainerFlexCol(
                self.content_area, self.banner, pos=(0, 8), padding_row=8
            )

        else:
            self.container = ContainerFlexCol(
                self.content_area, self.title, pos=(0, 40)
            )

        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_ata_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO_TOKEN_ACCOUNT__COLON),
            to,
        )
        self.item_group_body_from_ata_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM_TOKEN_ACCOUNT__COLON),
            from_addr,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee_payer = DisplayItem(
            self.group_fees, _(i18n_keys.LIST_KEY__FEE_PAYER__COLON), fee_payer
        )
        # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_signer = DisplayItem(
            self.group_more, _(i18n_keys.LIST_KEY__SIGNER__COLON), source_owner
        )
        if token_mint:
            self.item_group_body_mint_addr = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__MINT_ADDRESS), token_mint
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class BlindingSignCommon(FullSizeWindow):
    def __init__(self, signer: str, primary_color, icon_path):
        super().__init__(
            _(i18n_keys.TITLE__VIEW_TRANSACTION),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.warning_banner = Banner(
            self.content_area,
            BannerType.Warning,
            _(i18n_keys.TITLE__UNKNOWN_TRANSACTION),
        )
        self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(self.content_area, self.title, padding_row=0)
        self.container.align_to(self.warning_banner, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
        # self.container.add_dummy()
        self.item_format = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__FORMAT__COLON),
            _(i18n_keys.LIST_VALUE__UNKNOWN__COLON),
        )
        self.item_signer = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__SIGNER__COLON), signer
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class Modal(FullSizeWindow):
    def __init__(
        self,
        title: str | None,
        subtitle: str | None,
        confirm_text: str = "",
        cancel_text: str = "",
        icon_path: str | None = None,
        anim_dir: int = 0,
        nav_back=True,
    ):
        super().__init__(
            title,
            subtitle,
            confirm_text,
            cancel_text,
            icon_path,
            anim_dir=anim_dir,
            nav_back=nav_back,
        )

    def show_unload_anim(self):
        self.destroy(300)


class AlgoCommon(FullSizeWindow):
    def __init__(self, type: str, primary_color, icon_path):
        super().__init__(
            _(i18n_keys.TITLE__VIEW_TRANSACTION),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item_type = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__TYPE__COLON),
            type,
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoPayment(FullSizeWindow):
    def __init__(
        self,
        title,
        sender,
        receiver,
        close_to,
        rekey_to,
        genesis_id,
        note,
        fee,
        amount,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(self.group_amounts, None, amount)
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            receiver,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        if any([close_to, rekey_to, genesis_id]):
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if close_to is not None:
                self.item_close_reminder_to = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CLOSE_REMAINDER_TO__COLON),
                    close_to,
                )
            if rekey_to is not None:
                self.item_rekey_to = DisplayItem(
                    self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
                )
            if genesis_id is not None:
                self.item_genesis_id = DisplayItem(
                    self.group_more, "GENESIS ID:", genesis_id
                )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoAssetFreeze(FullSizeWindow):
    def __init__(
        self,
        sender,
        rekey_to,
        fee,
        index,
        target,
        new_freeze_state,
        genesis_id,
        note,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("ALGO"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_asset_freeze_state = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__FREEZE_ASSET_ID__COLON),
            _(i18n_keys.LIST_VALUE__TRUE)
            if new_freeze_state is True
            else _(i18n_keys.LIST_VALUE__FALSE),
        )
        self.item_group_freeze_account = DisplayItem(
            self.group_more, _(i18n_keys.LIST_KEY__FREEZE_ACCOUNT__COLON), target
        )
        self.item_group_body_asset_id = DisplayItem(
            self.group_more, _(i18n_keys.LIST_KEY__ASSET_ID__COLON), index
        )
        if rekey_to is not None:
            self.item_rekey_to = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
            )
        if genesis_id is not None:
            self.item_genesis_id = DisplayItem(
                self.group_more, "GENESIS ID:", genesis_id
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoAssetXfer(FullSizeWindow):
    def __init__(
        self,
        title,
        sender,
        receiver,
        index,
        fee,
        amount,
        close_assets_to,
        revocation_target,
        rekey_to,
        genesis_id,
        note,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(self.group_amounts, None, amount)
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            receiver,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        if revocation_target is not None:
            self.item_group_body_revocation_addr = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__REVOCATION_ADDRESS__COLON),
                revocation_target,
            )
        self.item_group_body_asset_id = DisplayItem(
            self.group_more, _(i18n_keys.LIST_KEY__ASSET_ID__COLON), index
        )
        if rekey_to is not None:
            self.item_rekey_to = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
            )
        if close_assets_to is not None:
            self.item_close_assets_to = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CLOSE_ASSET_TO__COLON),
                close_assets_to,
            )
        if genesis_id is not None:
            self.item_genesis_id = DisplayItem(
                self.group_more, "GENESIS ID:", genesis_id
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoAssetCfg(FullSizeWindow):
    def __init__(
        self,
        fee,
        sender,
        index,
        total,
        default_frozen,
        unit_name,
        asset_name,
        decimals,
        manager,
        reserve,
        freeze,
        clawback,
        url,
        metadata_hash,
        rekey_to,
        genesis_id,
        note,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("ALGO"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if url is not None:
            self.banner = Banner(
                self.content_area,
                BannerType.Default,
                _(i18n_keys.LIST_KEY__INTERACT_WITH).format(url),
            )
            self.banner.align(self.lv.ALIGN.TOP_MID, 0, 40)
            self.container.align_to(self.banner, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        if any(
            [
                asset_name,
                index,
                manager,
                reserve,
                freeze,
                clawback,
                default_frozen,
                freeze,
                total,
                decimals,
                unit_name,
                metadata_hash,
                rekey_to,
                genesis_id,
            ]
        ):
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if asset_name is not None:
                self.item_group_body_asset_name = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__ASSET_NAME__COLON),
                    asset_name,
                )
            if unit_name is not None:
                self.item_group_body_unit_name = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__UNIT_NAME__COLON),
                    unit_name,
                )
            if index is not None and index != "0":
                self.item_group_body_asset_id = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__ASSET_ID__COLON),
                    index,
                )
            if clawback is not None:
                self.item_group_body_clawback_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__CLAW_BACK_ADDRESS__COLON),
                    clawback,
                )
            if manager is not None:
                self.item_group_body_manager_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__MANAGER_ADDRESS__COLON),
                    manager,
                )
            if reserve is not None:
                self.item_group_body_reserve_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__RESERVE_ADDRESS__COLON),
                    reserve,
                )
            if default_frozen is not None:
                self.item_group_body_default_frozen = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__FREEZE_ADDRESS__QUESTION),
                    _(i18n_keys.LIST_VALUE__TRUE)
                    if default_frozen is True
                    else _(i18n_keys.LIST_VALUE__FALSE),
                )
            if freeze is not None:
                self.item_group_body_freeze_addr = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__FREEZE_ADDRESS__COLON),
                    freeze,
                )
            if decimals is not None and decimals != "0":
                self.item_group_body_decimals = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__DECIMALS__COLON),
                    decimals,
                )
            if total is not None:
                self.item_group_body_total = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__TOTAL__COLON),
                    total,
                )
            if metadata_hash is not None:
                self.item_group_body_metadata_hash = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__METADATA_HASH__COLON),
                    metadata_hash,
                )
            if rekey_to is not None:
                self.item_rekey_to = DisplayItem(
                    self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
                )
            if genesis_id is not None:
                self.item_genesis_id = DisplayItem(
                    self.group_more, "GENESIS ID:", genesis_id
                )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoKeyregOnline(FullSizeWindow):
    def __init__(
        self,
        sender,
        fee,
        votekey,
        selkey,
        sprfkey,
        rekey_to,
        genesis_id,
        note,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("ALGO"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_vrf_public_key = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__VRF_PUBLIC_KEY__COLON),
            selkey,
        )
        self.item_group_body_vote_public_key = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__VOTE_PUBLIC_KEY__COLON),
            votekey,
        )
        if sprfkey is not None:
            self.item_group_body_sprf_public_key = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__STATE_PROOF_PUBLIC_KEY__COLON),
                sprfkey,
            )
        if rekey_to is not None:
            self.item_rekey_to = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
            )
        if genesis_id is not None:
            self.item_genesis_id = DisplayItem(
                self.group_more, "GENESIS ID:", genesis_id
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoKeyregNonp(FullSizeWindow):
    def __init__(self, sender, fee, nonpart, rekey_to, genesis_id, note, primary_color):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("ALGO"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee,
        )
        # self.group_fees.add_dummy()

        if note:
            self.item_note = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__NOTE__COLON),
                note,
                theme_path_png("group-icon-data"),
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_nonpart = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__NONPARTICIPATION__COLON),
            _(i18n_keys.LIST_VALUE__FALSE)
            if nonpart is True
            else _(i18n_keys.LIST_VALUE__TRUE),
        )
        if rekey_to is not None:
            self.item_rekey_to = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__REKEY_TO__COLON), rekey_to
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AlgoApplication(FullSizeWindow):
    def __init__(self, signer: str, primary_color, icon_path):
        super().__init__(
            _(i18n_keys.TITLE__VIEW_TRANSACTION),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        self.item1 = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__FORMAT__COLON),
            "Application",
        )
        self.item2 = DisplayItem(
            self.container, _(i18n_keys.LIST_KEY__SIGNER__COLON), signer
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class RipplePayment(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        fee_max,
        total_amount=None,
        tag=None,
        primary_color=None,
        icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            fee_max,
        )
        if total_amount is None:
            total_amount = f"{amount}\n{fee_max}"
        self.item_group_body_total_amount = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
            total_amount,
        )
        # self.group_fees.add_dummy()

        if tag:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            self.item_group_body_tag = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__DESTINATION_TAG__COLON),
                tag,
            )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class NftRemoveConfirm(FullSizeWindow):
    def __init__(self, icon_path):
        super().__init__(
            title=_(i18n_keys.TITLE__REMOVE_NFT),
            subtitle=_(i18n_keys.SUBTITLE__REMOVE_NFT),
            confirm_text=_(i18n_keys.BUTTON__REMOVE),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            icon_path=icon_path,
            anim_dir=0,
            button_layout=1,
        )
        self.btn_yes.enable(
            bg_color=lv_theme.APP_ERROR_BG, text_color=lv_theme.BTN_YES_FG
        )

    def destroy(self, _delay_ms=400):
        self.del_delayed(200)


class FilecoinPayment(FullSizeWindow):
    def __init__(
        self,
        title,
        address_from,
        address_to,
        amount,
        gaslimit,
        gasfeecap=None,
        gaspremium=None,
        total_amount=None,
        primary_color=None,
        icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_gas_limit = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__GAS_LIMIT__COLON),
            gaslimit,
        )
        self.item_group_body_gas_cap = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__GAS_FEE_CAP__COLON),
            gasfeecap,
        )
        self.item_group_body_gas_premium = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__GAS_PREMIUM__COLON),
            gaspremium,
        )
        self.item_group_body_total_amount = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__TOTAL_AMOUNT__COLON),
            total_amount,
        )
        # self.group_fees.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosTransactionOverview(FullSizeWindow):
    def __init__(
        self,
        title,
        types,
        value,
        amount,
        address,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            anim_dir=2,
            primary_color=primary_color,
            icon_path=theme_path("send.png") if types is None else icon_path,
            sub_icon_path=icon_path if types is None else None,
            # button_layout=1
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        if types is None:
            if striped:
                self.group_amounts = ContainerFlexCol(
                    self.container, None, padding_row=0, no_align=True
                )
                self.item_group_header = CardHeader(
                    self.group_amounts,
                    _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                    theme_path_png("group-icon-amount"),
                )
                self.item_group_body_amount = DisplayItem(
                    self.group_amounts,
                    None,
                    amount,
                )
                # self.group_amounts.add_dummy()

            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.FORM__DIRECTIONS),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_to_addr = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__TO__COLON),
                address,
            )
            # self.group_directions.add_dummy()
        else:
            self.container.add_style(StyleWrapper().pad_row(0), 0)
            # self.container.add_dummy()
            self.item_type = DisplayItem(
                self.container,
                _(i18n_keys.LIST_KEY__TYPE__COLON),
                value,
            )
            # self.container.add_dummy()

        self.view_btn = NormalButton(
            self.content_area,
            f"{LV_SYMBOLS.LV_SYMBOL_ANGLE_DOUBLE_DOWN}  {_(i18n_keys.BUTTON__DETAILS)}",
        )
        self.view_btn.set_size(450, 82)
        self.view_btn.add_style(StyleWrapper().text_font(font_GeistSemiBold26), 0)
        self.view_btn.enable()
        self.view_btn.align_to(self.container, lv.ALIGN.OUT_BOTTOM_MID, 0, 16)
        self.view_btn.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)
        # self.content_area.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.TEST_FG)
        #     .bg_opa(lv.OPA.COVER)
        #     , 0,
        # )
        # self.container.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.APP_WARNING_BG)
        #     .bg_opa(lv.OPA.COVER)
        #     , 0,
        # )
        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.view_btn:
                self.destroy(400)
                self.channel.publish(2)


class CosmosSend(FullSizeWindow):
    def __init__(
        self,
        title,
        chain_id,
        chain_name,
        address_from,
        address_to,
        amount,
        fee,
        memo,
        primary_color=None,
        icon_path=None,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            address_to,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            address_from,
        )
        # self.group_directions.add_dummy()

        if fee:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_fee = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__FEE__COLON),
                fee,
            )
            # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        if chain_name:
            self.item_group_body_chain_name = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CHAIN_NAME__COLON),
                chain_name,
            )
        else:
            self.item_group_body_chain_id = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__CHAIN_ID__COLON), chain_id
            )
        if memo:
            self.item_group_body_memo = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__MEMO__COLON),
                memo,
            )
        # self.group_more.add_dummy()

        # self.container.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.APP_WARNING_BG)
        #     .bg_opa(lv.OPA.COVER)
        #     , 0,
        # )
        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosDelegate(FullSizeWindow):
    def __init__(
        self,
        title,
        chain_id,
        chain_name,
        delegator,
        validator,
        amount,
        fee,
        memo,
        primary_color=None,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_amounts = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_amounts,
            _(i18n_keys.LIST_KEY__AMOUNT__COLON),
            theme_path_png("group-icon-amount"),
        )
        self.item_group_body_amount = DisplayItem(
            self.group_amounts,
            None,
            amount,
        )
        # self.group_amounts.add_dummy()

        if fee:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_fee = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__FEE__COLON),
                fee,
            )
            # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_delegator = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__DELEGATOR__COLON),
            delegator,
        )
        self.item_group_body_validator = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__VALIDATOR__COLON),
            validator,
        )

        if chain_name:
            self.item_group_body_chain_name = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CHAIN_NAME__COLON),
                chain_name,
            )
        else:
            self.item_group_body_chain_id = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__CHAIN_ID__COLON), chain_id
            )
        if memo:
            self.item_group_body_memo = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__MEMO__COLON),
                memo,
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosSignCommon(FullSizeWindow):
    def __init__(
        self,
        chain_id: str,
        chain_name: str,
        signer: str,
        fee: str,
        title: str,
        value: str,
        memo,
        primary_color,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if signer:
            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.FORM__DIRECTIONS),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_signer = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__SIGNER__COLON),
                signer,
            )
            # self.group_directions.add_dummy()

        if fee:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_fee = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__FEE__COLON),
                fee,
            )
            # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        if chain_name:
            self.item_group_body_chain_name = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__CHAIN_NAME__COLON),
                chain_name,
            )
        else:
            self.item_group_body_chain_id = DisplayItem(
                self.group_more, _(i18n_keys.LIST_KEY__CHAIN_ID__COLON), chain_id
            )
        self.item_group_body_type = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__TYPE__COLON),
            value,
        )
        if memo:
            self.item_group_body_memo = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__MEMO__COLON),
                memo,
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosSignContent(FullSizeWindow):
    def __init__(
        self,
        msgs_item: dict,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__CONTENT),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(
            self.content_area, self.title, pos=(0, 40), padding_row=0
        )
        # self.container.add_dummy()
        for key, value in msgs_item.items():
            if len(str(value)) <= 80:
                self.item = DisplayItem(self.container, key, str(value))
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosLongValue(FullSizeWindow):
    def __init__(
        self,
        title,
        content: str,
        primary_color,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color or lv_theme.APP_CORRECT_BG,
            button_layout=1,
        )
        self.primary_color = primary_color
        PageAbleMessage(
            title,
            content,
            self.channel,
            primary_color=self.primary_color,
        )
        self.destroy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class CosmosSignCombined(FullSizeWindow):
    def __init__(self, chain_id: str, signer: str, fee: str, data: str, primary_color):
        super().__init__(
            _(i18n_keys.TITLE__VIEW_TRANSACTION),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            button_layout=1,
        )
        self.primary_color = primary_color
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if signer:
            self.group_directions = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_directions,
                _(i18n_keys.FORM__DIRECTIONS),
                theme_path_png("group-icon-directions"),
            )
            self.item_group_body_signer = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__SIGNER__COLON),
                signer,
            )
            # self.group_directions.add_dummy()

        if fee:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_fee = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__FEE__COLON),
                fee,
            )
            # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_chain_id = DisplayItem(
            self.group_more, _(i18n_keys.LIST_KEY__CHAIN_ID__COLON), chain_id
        )
        # self.group_more.add_dummy()

        self.long_data = False
        self.data_str = data
        if len(data) > 225:
            self.long_data = True
            self.data = data[:222] + "..."
        else:
            self.data = data
        self.item_data = CardItem(
            self.container,
            _(i18n_keys.LIST_KEY__DATA__COLON),
            self.data,
            theme_path_png("group-icon-data"),
        )
        if self.long_data:
            self.show_full_data = NormalButton(
                self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
            )
            self.show_full_data.set_size(lv.SIZE.CONTENT, 82)
            self.show_full_data.add_style(
                StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
            )
            self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
            self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
            self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                )


class ConfirmTypedHash(FullSizeWindow):
    def __init__(self, title, icon, domain_hash, message_hash, primary_color):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            icon,
            primary_color=primary_color,
            anim_dir=0,
            button_layout=1,
        )
        self.banner = Banner(
            self.content_area,
            BannerType.Warning,
            _(i18n_keys.MSG__SIGNING_MSG_MAY_HAVE_RISK),
        )
        self.banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(self.content_area, self.title, padding_row=0)
        self.container.align_to(self.banner, lv.ALIGN.OUT_BOTTOM_MID, 0, 24)
        # self.container.add_dummy()
        self.item_separator_hash = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__DOMAIN_SEPARATOR_HASH__COLON),
            domain_hash,
        )
        self.item_message_hash = DisplayItem(
            self.container,
            _(i18n_keys.LIST_KEY__MESSAGE_HASH__COLON),
            message_hash,
        )
        # self.container.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class PolkadotBalances(FullSizeWindow):
    def __init__(
        self,
        title,
        chain_name,
        module,
        method,
        sender,
        dest,
        source,
        balance,
        tip,
        keep_alive,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 48))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                balance,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            dest,
        )

        self.item_group_body_signer = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__SIGNER__COLON),
            sender,
        )
        # self.group_directions.add_dummy()

        if tip:
            self.group_fees = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_fees,
                _(i18n_keys.FORM__FEES),
                theme_path_png("group-icon-fees"),
            )
            self.item_group_body_fee = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__TIP__COLON),
                tip,
            )
            # self.group_fees.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_chain_name = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__CHAIN_NAME__COLON),
            chain_name,
        )
        if source:
            self.item_group_body_source = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__SOURCE_COLON),
                source,
            )
        # if module:
        #     self.item_group_body_module = DisplayItem(
        #         self.group_more,
        #         _(i18n_keys.LIST_KEY__MODULE_COLON),
        #         module,
        #     )
        # if method:
        #     self.item_group_body_method = DisplayItem(
        #         self.group_more,
        #         _(i18n_keys.LIST_KEY__METHOD_COLON),
        #         method,
        #     )
        if keep_alive is not None:
            self.item_group_body_keep_alive = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__KEEP_ALIVE_COLON),
                keep_alive,
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AptosTransfer(FullSizeWindow):
    def __init__(
        self,
        title,
        sender,
        recipient,
        amount,
        max_fee,
        function,
        chain_id,
        token,
        signer,
        metadata,
        fee_payer,
        secondary_signers,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 48))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            recipient,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        if signer and signer != sender:
            self.item_group_body_signer = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__SIGNER__COLON),
                signer,
            )

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            max_fee,
        )
        if fee_payer:
            self.item_group_body_fee_payer = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__FEE_PAYER__COLON),
                fee_payer,
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        if token:
            self.item_group_body_token = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__TOKEN__COLON),
                token,
            )
        if metadata:
            self.item_group_body_metadata = DisplayItem(
                self.group_more,
                _(i18n_keys.TOKEN_ADDRESS),
                metadata,
            )
        if function:
            self.item_group_body_function = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__FUNCTION__COLON),
                function,
            )
        self.item_group_body_chain_id = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__CHAIN_ID__COLON),
            chain_id,
        )
        if secondary_signers:
            self.item_group_body_secondary_signers = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__SECONDARY_SIGNERS__COLON),
                secondary_signers,
            )


class SuiTransfer(FullSizeWindow):
    def __init__(
        self,
        title,
        sender,
        recipient,
        amount,
        max_fee,
        gas_owner,
        gas_price,
        gas_budget,
        signer,
        tx_type,
        token,
        primary_color,
        icon_path,
        striped=False,
    ):
        super().__init__(
            title,
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__CANCEL),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 48))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.item_group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            recipient,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        if signer and signer != sender:
            self.item_group_body_signer = DisplayItem(
                self.group_directions,
                _(i18n_keys.LIST_KEY__SIGNER__COLON),
                signer,
            )

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__MAXIMUM_FEE__COLON),
            max_fee,
        )
        if gas_owner and gas_owner != sender:
            self.item_group_body_gas_owner = DisplayItem(
                self.group_fees,
                _(i18n_keys.LIST_KEY__GAS_OWNER__COLON),
                gas_owner,
            )

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_body_tx_type = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__TYPE__COLON),
            tx_type,
        )
        if token:
            self.item_group_body_token = DisplayItem(
                self.group_more,
                _(i18n_keys.LIST_KEY__TOKEN__COLON),
                token,
            )
        self.item_group_body_gas_price = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
            gas_price,
        )
        self.item_group_body_gas_budget = DisplayItem(
            self.group_more,
            _(i18n_keys.LIST_KEY__GAS_BUDGET__COLON),
            gas_budget,
        )


class TronAssetFreeze(FullSizeWindow):
    def __init__(
        self,
        is_freeze,
        sender,
        resource,
        balance,
        duration,
        receiver,
        lock,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("Tron"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            sender,
        )
        # self.group_directions.add_dummy()
        if any((resource, balance, receiver, duration, lock)):
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            if resource is not None:
                self.item_body_resource = DisplayItem(
                    self.group_more, _(i18n_keys.LIST_KEY__RESOURCE_COLON), resource
                )
            if balance:
                if is_freeze:
                    self.item_body_freeze_balance = DisplayItem(
                        self.group_more,
                        _(i18n_keys.LIST_KEY__FROZEN_BALANCE_COLON),
                        balance,
                    )
                else:
                    self.item_body_balance = DisplayItem(
                        self.group_more,
                        _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                        balance,
                    )
            if duration:
                self.item_body_duration = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__FROZEN_DURATION_COLON),
                    duration,
                )
            if receiver is not None:
                self.item_body_receiver = DisplayItem(
                    self.group_more,
                    _(i18n_keys.LIST_KEY__RECEIVER_ADDRESS_COLON),
                    receiver,
                )
            if lock is not None:
                self.item_body_lock = DisplayItem(
                    self.group_more, _(i18n_keys.LIST_KEY__LOCK_COLON), lock
                )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class TronVoteWitness(FullSizeWindow):
    def __init__(
        self,
        voter,
        votes,
        primary_color,
    ):
        super().__init__(
            _(i18n_keys.TITLE__SIGN_STR_TRANSACTION).format("Tron"),
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_voter = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__VOTER__COLON),
            voter,
        )
        # self.group_directions.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        multi_vote = len(votes) > 1
        for i, (candidate, count) in enumerate(votes):
            self.item_group_body_vote = DisplayItem(
                self.group_more,
                f"{_(i18n_keys.GLOBAL_CANDIDATE)} #{i + 1}"
                if multi_vote
                else _(i18n_keys.GLOBAL_CANDIDATE),
                candidate,
            )
            self.item_group_body_vote.label_top.set_recolor(False)
            self.item_group_body_vote_count = DisplayItem(
                self.group_more,
                _(i18n_keys.GLOBAL__VOTE_COUNT),
                str(count),
            )
        # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class NeoTokenTransfer(FullSizeWindow):
    def __init__(
        self,
        title,
        from_addr: str,
        to_addr: str,
        amount: str,
        fee: str,
        primary_color,
        icon_path,
        striped: bool = False,
        network_magic: int | None = None,
    ):
        super().__init__(
            title,
            subtitle=None,
            confirm_text=_(i18n_keys.BUTTON__CONTINUE),
            cancel_text=_(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=theme_path("send.png"),
            sub_icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        if striped:
            self.group_amounts = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_amounts,
                _(i18n_keys.LIST_KEY__AMOUNT__COLON),
                theme_path_png("group-icon-amount"),
            )
            self.group_body_amount = DisplayItem(
                self.group_amounts,
                None,
                amount,
            )
            # self.group_amounts.add_dummy()

        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            to_addr,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__FROM__COLON),
            from_addr,
        )
        # self.group_directions.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_fee = DisplayItem(
            self.group_fees, _(i18n_keys.LIST_KEY__FEE__COLON), fee
        )
        # self.group_fees.add_dummy()
        if network_magic:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            self.item_group_body_network_magic = DisplayItem(
                self.group_more, _(i18n_keys.GLOBAL_TARGET_NETWORK), str(network_magic)
            )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class NeoVote(FullSizeWindow):
    def __init__(
        self,
        from_address: str,
        vote_to: str,
        is_remove_vote: bool,
        primary_color,
        icon_path,
        network_magic: int | None = None,
    ):
        super().__init__(
            f"Neo {_(i18n_keys.TITLE__VOTE)}"
            if not is_remove_vote
            else f"Neo {_(i18n_keys.TITLE_REMOVE_VOTE)}",
            None,
            _(i18n_keys.BUTTON__CONTINUE),
            _(i18n_keys.BUTTON__REJECT),
            primary_color=primary_color,
            icon_path=icon_path,
            button_layout=1,
        )
        self.container = ContainerFlexCol(self.content_area, self.title, pos=(0, 40))
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        if not is_remove_vote:
            self.item_group_body_vote_to = DisplayItem(
                self.group_directions,
                _(i18n_keys.GLOBAL_CANDIDATE),
                vote_to,
            )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__VOTER__COLON),
            from_address,
        )
        # self.group_directions.add_dummy()
        if network_magic:
            self.group_more = ContainerFlexCol(
                self.container, None, padding_row=0, no_align=True
            )
            self.item_group_header = CardHeader(
                self.group_more,
                _(i18n_keys.FORM__MORE),
                theme_path_png("group-icon-more"),
            )
            self.item_group_body_network_magic = DisplayItem(
                self.group_more, _(i18n_keys.GLOBAL_TARGET_NETWORK), str(network_magic)
            )
            # self.group_more.add_dummy()

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class UrResponse(FullSizeWindow):
    def __init__(
        self,
        title,
        subtitle,
        qr_code,
        encoder=None,
    ):
        super().__init__(
            title,
            subtitle,
            confirm_text=_(i18n_keys.BUTTON__DONE),
            anim_dir=0,
            button_layout=1,
        )
        self.btn_yes.enable(lv_theme.BTN_YES_BG, text_color=lv_theme.BTN_YES_FG)

        gc.collect()
        self.qr_code = qr_code
        self.encoder = encoder
        self.qr = QRCode(
            self.content_area,
            self.qr_code if self.qr_code else encoder.next_part(),  # type: ignore["next_part" is not a known member of "None"]
            size=440,
        )
        self.qr.align_to(self.nav_back, lv.ALIGN.OUT_BOTTOM_LEFT, 15, 20)
        self.subtitle.align_to(self.qr, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 30)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.content_area.clear_flag(lv.obj.FLAG.SCROLL_MOMENTUM)
        self.content_area.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        if encoder is not None:
            from trezor import workflow

            workflow.spawn(self.update_qr())

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def destroy(self, delay_ms=400):
        return self.delete()

    async def update_qr(self):
        from trezor import loop

        while True:
            stop_single = self.request()
            racer = loop.race(stop_single, loop.sleep(100))
            await racer
            if stop_single in racer.finished:
                self.destroy()
                return
            # if self.scrolling:
            #     await loop.sleep(5000)
            #     continue
            qr_data = self.encoder.next_part()  # type: ignore["next_part" is not a known member of "None"]
            self.qr.update(qr_data, len(qr_data))


class ErrorFeedback(FullSizeWindow):
    def __init__(self, title, subtitle, btn_text: str = ""):
        super().__init__(
            title,
            subtitle,
            cancel_text=_(i18n_keys.BUTTON__BACK) if not btn_text else btn_text,
            icon_path=theme_path_png("danger"),
            button_layout=1,
        )

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def destroy(self):
        return super().destroy(100)


##################
# misc functions #
##################
class AirgapMode(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__AIR_GAP_MODE),
            _(i18n_keys.CONTENT__WHAT_DOES_AIR_GAP_MEANS),
            _(i18n_keys.BUTTON__SKIP),
            _(i18n_keys.BUTTON__GO_SETTING),
            button_layout=1,
        )
        self.btn_yes.enable()
        self.btn_no.enable(
            bg_color=lv_theme.APP_CORRECT_BG, text_color=lv_theme.BTN_YES_FG
        )

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)


class AirGapToggleTips(FullSizeWindow):
    def __init__(self, enable, callback_obj=None):
        super().__init__(
            title=_(i18n_keys.TITLE__ENABLE_AIR_GAP)
            if enable
            else _(i18n_keys.TITLE__DISABLE_AIR_GAP),
            subtitle=_(i18n_keys.CONTENT__ARE_YOU_SURE_TO_ENABLE_AIRGAP_MODE)
            if enable
            else _(i18n_keys.CONTENT__ARE_YOU_SURE_TO_DISABLE_AIRGAP_MODE),
            confirm_text=_(i18n_keys.BUTTON__ENABLE)
            if enable
            else _(i18n_keys.BUTTON__DISABLE),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            anim_dir=0,
            button_layout=1,
        )
        self.last_click_time = 0
        self.click_interval = 1000
        self.callback_obj = callback_obj

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def eventhandler(self, event_obj):
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, self.last_click_time) < self.click_interval:
            return
        self.last_click_time = current_time
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            elif target == self.btn_no:
                if self.callback_obj:
                    lv.event_send(self.callback_obj, lv.EVENT.CANCEL, None)
                else:
                    self.channel.publish(0)
            elif target == self.btn_yes:
                if self.callback_obj:
                    lv.event_send(self.callback_obj, lv.EVENT.READY, None)
                else:
                    self.channel.publish(1)
            elif target in (self.nav_back, self.nav_back.nav_btn):
                self.show_dismiss_anim()
                self.channel.publish(0)
            else:
                return
            self.show_dismiss_anim()

    def destroy(self, delay_ms=100):
        return self.del_delayed(100)


class ConnectWalletTutorial(FullSizeWindow):
    def __init__(
        self,
        title: str,
        sub_title,
        steps: list[tuple[str, str]],
        website_url,
        logo_path,
    ):
        super().__init__(
            title,
            sub_title,
            confirm_text=_(i18n_keys.BUTTON__DONE),
            cancel_text=_(i18n_keys.ACTION__LEARN_MORE),
            anim_dir=0,
            button_layout=1,
        )
        self.website_url = website_url
        self.logo_path = logo_path

        self.container = ContainerFlexCol(
            self.content_area, self.subtitle, pos=(0, 40), padding_row=0
        )
        self.container.add_style(StyleWrapper().bg_opa(lv.OPA.COVER).pad_bottom(15), 0)
        for i, step in enumerate(steps):
            self.item_group_body = DisplayItem(
                self.container,
                step[0],
                step[1],
                bot_line=True if i < len(steps) - 1 else False,
                title_index=i + 1,
                font_space=0,
                padding_ver=0,
            )
            self.item_group_body.add_style(
                StyleWrapper().pad_top(15).bg_opa(lv.OPA.TRANSP), 0
            )

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return
            if target == self.btn_yes:
                self.destroy(10)
            elif target == self.btn_no:
                ConnectWalletTutorial.ShowOnlineWebsiteQR(
                    self.website_url, self.logo_path
                )
            elif target in (self.nav_back.nav_btn, self.nav_back):
                if not hasattr(self, "on_nav_back"):
                    self.show_dismiss_anim()
                    self.channel.publish(0)

    class ShowOnlineWebsiteQR(FullSizeWindow):
        def __init__(self, qr_content: str, logo_path):
            super().__init__(
                None,
                None,
                anim_dir=0,
                cancel_text=_(i18n_keys.BUTTON__CLOSE),
                button_layout=1,
            )

            gc.collect()
            self.qr = QRCode(self.content_area, qr_content, logo_path)
            self.qr.align_to(self.content_area, lv.ALIGN.TOP_MID, 0, 16)

            self.desc = lv.label(self.content_area)
            self.desc.set_size(450, lv.SIZE.CONTENT)
            self.desc.set_long_mode(lv.label.LONG.WRAP)
            self.desc.add_style(
                StyleWrapper()
                .text_font(font_GeistRegular30)
                .text_color(lv_theme.DT_DESC_FG)
                .pad_hor(15)
                .text_align_center()
                .pad_ver(15),
                0,
            )
            self.desc.set_text(
                _(i18n_keys.CONTENT__SCAN_THE_QR_CODE_TO_VIEW_THE_DETAILED_TUTORIAL)
            )
            self.desc.align_to(self.qr, lv.ALIGN.OUT_BOTTOM_MID, 0, 8)

            # self.content_area.set_style_min_height(660, 0)
            # self.update_btn_layout()
            # if hasattr(self, "bnt_container") and self.bnt_container:
            #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

        def eventhandler(self, event_obj):
            code = event_obj.code
            target = event_obj.get_target()
            if code == lv.EVENT.CLICKED:
                if utils.lcd_resume():
                    return
                if target == self.btn_no:
                    self.destroy(10)
                elif target in (self.nav_back, self.nav_back.nav_btn):
                    self.show_dismiss_anim()
                    self.channel.publish(0)


class GnosisSafeTxDetails(FullSizeWindow):
    def __init__(
        self,
        from_address: str,
        to_address: str,
        value: str,
        call_data: bytes | None,
        operation: int,
        safe_tx_gas: int,
        base_gas: int,
        gas_price: str,
        gas_token: str,
        refund_receiver: str,
        nonce: int,
        verifying_contract: str,
        icon_path: str,
        primary_color: str,
        domain_hash: str,
        message_hash: str,
        safe_tx_hash: str,
    ):
        super().__init__(
            _(i18n_keys.GNOSIS_SAFE_SIG_TITLE),
            None,
            _(i18n_keys.BUTTON__CONFIRM),
            _(i18n_keys.BUTTON__REJECT),
            icon_path=icon_path,
            primary_color=primary_color,
            button_layout=1,
        )
        self.primary_color = primary_color
        is_delegate_call = operation == 1
        if is_delegate_call:
            self.warning_banner = Banner(
                self.content_area,
                BannerType.Danger,
                _(i18n_keys.GNOSIS_SAFE_SIG_DELEGATECALL_WARNING_TEXT),
            )
            self.warning_banner.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.container = ContainerFlexCol(
            self.content_area,
            self.title if not is_delegate_call else self.warning_banner,
            pos=(0, 40 if not is_delegate_call else 8),
        )
        self.group_directions = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_directions,
            _(i18n_keys.FORM__DIRECTIONS),
            theme_path_png("group-icon-directions"),
        )
        self.group_body_amount = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__AMOUNT__COLON),
            value,
        )
        self.item_group_body_to_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__TO__COLON),
            to_address,
        )
        self.item_group_body_from_addr = DisplayItem(
            self.group_directions,
            _(i18n_keys.LIST_KEY__SIGNER__COLON),
            from_address,
        )
        # self.group_directions.add_dummy()

        self.group_more = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_more,
            _(i18n_keys.FORM__MORE),
            theme_path_png("group-icon-more"),
        )
        self.item_group_operation = DisplayItem(
            self.group_more,
            _(i18n_keys.GLOBAL_OPERATION),
            "0 (CALL)" if operation == 0 else "#FF1100 1 (DELEGATECALL)#",
        )
        self.item_group_nonce = DisplayItem(
            self.group_more,
            "Nonce",
            str(nonce),
        )
        self.item_group_verifying_contract = DisplayItem(
            self.group_more,
            "VerifyingContract",
            verifying_contract,
        )
        # self.group_more.add_dummy()

        self.group_hash = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_hash,
            "Hash",
            theme_path_png("group-icon-more"),
        )
        self.item_group_domain_hash = DisplayItem(
            self.group_hash,
            "DomainHash",
            domain_hash,
        )
        self.item_group_message_hash = DisplayItem(
            self.group_hash,
            "MessageHash",
            message_hash,
        )
        self.item_group_safe_tx_hash = DisplayItem(
            self.group_hash,
            "SafeTxHash",
            safe_tx_hash,
        )
        # self.group_hash.add_dummy()

        self.group_fees = ContainerFlexCol(
            self.container, None, padding_row=0, no_align=True
        )
        self.item_group_header = CardHeader(
            self.group_fees,
            _(i18n_keys.FORM__FEES),
            theme_path_png("group-icon-fees"),
        )
        self.item_group_body_safe_tx_gas = DisplayItem(
            self.group_fees,
            _(i18n_keys.GNOSIS_SAGE_SIG_SAFE_TX_GAS),
            str(safe_tx_gas),
        )
        self.item_group_body_base_gas = DisplayItem(
            self.group_fees,
            _(i18n_keys.GLOBAL_BASE_GAS),
            str(base_gas),
        )
        self.item_group_body_gas_price = DisplayItem(
            self.group_fees,
            _(i18n_keys.LIST_KEY__GAS_PRICE__COLON),
            gas_price,
        )
        self.item_group_body_gas_token = DisplayItem(
            self.group_fees,
            _(i18n_keys.GLOBAL_GAS_TOKEN),
            gas_token,
        )
        self.item_group_body_refund = DisplayItem(
            self.group_fees,
            _(i18n_keys.GNOSIS_SAGE_SIG_REFUND_RECEIVER),
            refund_receiver,
        )
        # self.group_fees.add_dummy()

        if call_data:
            from trezor import strings

            self.data_str = strings.format_customer_data(call_data)
            if not self.data_str:
                return
            self.long_data = False
            if len(self.data_str) > 225:
                self.long_data = True
                self.data = self.data_str[:222] + "..."
            else:
                self.data = self.data_str
            self.item_data = CardItem(
                self.container,
                _(i18n_keys.LIST_KEY__DATA__COLON),
                self.data,
                theme_path_png("group-icon-data"),
            )
            if self.long_data:
                self.show_full_data = NormalButton(
                    self.item_data.content, _(i18n_keys.BUTTON__VIEW_DATA)
                )
                self.show_full_data.set_size(lv.SIZE.CONTENT, 77)
                self.show_full_data.add_style(
                    StyleWrapper().text_font(font_GeistSemiBold26).pad_hor(24), 0
                )
                self.show_full_data.align(lv.ALIGN.CENTER, 0, 0)
                self.show_full_data.remove_style(None, lv.PART.MAIN | lv.STATE.PRESSED)
                self.show_full_data.add_event_cb(self.on_click, lv.EVENT.CLICKED, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_click(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.show_full_data:
                PageAbleMessage(
                    _(i18n_keys.TITLE__VIEW_DATA),
                    self.data_str,
                    None,
                    primary_color=self.primary_color,
                    font=font_GeistMono28,
                    confirm_text=None,
                    cancel_text=None,
                    page_size=351,
                )


class Turbo(FullSizeWindow):
    def __init__(
        self,
        message_text=_(i18n_keys.MSG__UNKNOWN_MESSAGE),
        chain_name=_(i18n_keys.MSG__UNKNOWN_NETWORK),
        primary_color=lv_theme.APP_CORRECT_BG,
        icon_path="tools_turbo-send",
    ):
        super().__init__(
            None,
            None,
            nav_back=False,
        )

        gc.threshold(int(18248 * 1.5))  # type: ignore["threshold" is not a known member of module]
        gc.collect()

        self.gif_done_triggered = False

        self.content_area.set_style_max_height(800, 0)
        self.content_area.set_size(480, 800)
        self.content_area.set_style_bg_img_src(
            theme_path_default("tools_turbo-bg.png"), 0
        )
        # self.content_area.add_style(
        #     StyleWrapper()
        #     .bg_color(lv_theme.DT_BG)
        #     ,0,
        # )

        self.content_area.align(lv.ALIGN.TOP_MID, 0, 0)

        from .components.navigation import Navigation

        self.nav_back = Navigation(
            self.content_area,
            btn_bg_img=theme_path_png("cancel"),
            nav_btn_align=lv.ALIGN.RIGHT_MID,
            align=lv.ALIGN.TOP_RIGHT,
        )
        self.nav_back.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)

        from .components.label import Title

        self.title = Title(
            self.content_area,
            self.content_area,
            "Turbo mode",
            relative_type=lv.ALIGN.TOP_MID,
            relative_pos=(0, 100),
        )
        self.title.text.add_style(
            StyleWrapper()
            .text_color(lv_theme.APP_WHITE_FG)
            .text_font(font_GeistSemiBold48)
            .bg_opa(lv.OPA.TRANSP),
            0,
        )
        self.icon = lv.img(self.content_area)
        self.icon.set_src(theme_path_default(f"{icon_path}.png"))
        self.icon.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 50)

        self.chain_name = lv.label(self.content_area)
        self.chain_name.set_text(chain_name)
        self.chain_name.add_style(
            StyleWrapper()
            .text_color(lv_theme.APP_WHITE_FG)
            .text_font(font_GeistMono38)
            .bg_opa(lv.OPA.TRANSP),
            0,
        )
        self.chain_name.align_to(self.icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)
        self.message_text = lv.label(self.content_area)
        self.message_text.set_text(message_text)
        self.message_text.add_style(
            StyleWrapper()
            .text_color(lv_theme.APP_WHITE_FG)
            .text_font(font_GeistSemiBold48)
            .bg_opa(lv.OPA.TRANSP),
            0,
        )
        self.message_text.align_to(self.chain_name, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

        # from .components.listitem import ShortInfoItem
        # self.info_item = ShortInfoItem(
        #     parent=self.content_area,
        #     img_src=icon_path,
        #     title_text=message_text,
        #     subtitle_text=chain_name,
        #     bg_color=lv_theme.CONT_ITEM_BG,
        #     icon_boarder_color=primary_color,
        # )
        # self.info_item.align_to(self.title, lv.ALIGN.OUT_BOTTOM_MID, 0, 50)

        self.gif_loop = lv.gif(self.content_area)
        self.gif_loop.set_src(theme_path_default("tools_turbo-loop.gif"))
        self.gif_loop.align_to(self.message_text, lv.ALIGN.OUT_BOTTOM_MID, 0, 82)
        self.gif_loop.set_loop_count(15)
        self.gif_loop.add_event_cb(self._on_gif_loop_complete, lv.EVENT.READY, None)
        gc.collect()

        click_style = (
            StyleWrapper()
            .bg_opa(lv.OPA._30)
            .bg_color(lv_theme.DTL_BG)
            .border_opa(lv.OPA.TRANSP)
            .radius(100)
        )

        self.gif_mask = lv.obj(self.content_area)
        self.gif_mask.set_size(150, 150)
        self.gif_mask.align_to(self.gif_loop, lv.ALIGN.CENTER, 0, 0)

        self.gif_mask.add_style(
            StyleWrapper().bg_opa(lv.OPA.TRANSP).radius(75).border_opa(lv.OPA.TRANSP),
            0,
        )

        self.gif_mask.add_style(click_style, lv.STATE.PRESSED)

        self.gif_mask.add_flag(lv.obj.FLAG.CLICKABLE)
        self.gif_mask.add_event_cb(self.eventhandler, lv.EVENT.CLICKED, None)
        self.gif_mask.add_event_cb(self.eventhandler, lv.EVENT.PRESSED, None)

        self.tip_text = lv.label(self.content_area)
        self.tip_text.set_text(_(i18n_keys.ITEM__TAP_TO_SEND))
        self.tip_text.add_style(
            StyleWrapper()
            .text_font(font_GeistRegular20)
            .text_color(lv_theme.DT_TIP_FG)
            .pad_hor(12)
            .pad_ver(16),
            0,
        )
        self.tip_text.align_to(self.gif_mask, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)

        # self.content_area.set_style_min_height(660, 0)
        # # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def _on_gif_loop_complete(self, event_obj=None):
        self.destroy()
        self.channel.publish(0)

    def _on_gif_click(self, event_obj=None):
        if self.gif_done_triggered:
            return

        self.gif_done_triggered = True

        self.gif_mask.clear_flag(lv.obj.FLAG.CLICKABLE)

        if hasattr(self, "gif_loop"):
            self.gif_loop.del_delayed(0)

        self._start_completion_animation()

    def _start_completion_animation(self):
        self.gif_done = lv.gif(self.content_area)
        self.gif_done.set_src(theme_path_default("tools_turbo-done.gif"))
        self.gif_done.align_to(self.message_text, lv.ALIGN.OUT_BOTTOM_MID, 0, 82)
        self.gif_done.set_loop_count(1)
        self.gif_done.add_event_cb(self._on_completion_finished, lv.EVENT.READY, None)

    def _on_completion_finished(self, event_obj=None):
        self.destroy()
        self.channel.publish(1)

    def eventhandler(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()

        if code == lv.EVENT.PRESSED:
            gc.collect()
            if target == self.gif_mask:
                motor.vibrate(motor.WHISPER)
        if code == lv.EVENT.CLICKED:
            if utils.lcd_resume():
                return

            if target in (self.nav_back.nav_btn, self.nav_back):
                self.destroy(200)
                self.channel.publish(0)
            elif target == self.gif_mask:
                motor.vibrate(motor.SUCCESS)
                self._on_gif_click(event_obj)


class CertificationInfo(FullSizeWindow):
    class CertificationItem(lv.obj):
        def __init__(
            self,
            parent,
            left_text: str,
            right_text: str | None,
            icon_path: str | None = None,
            right_text_color=lv_theme.CONT_ITEM_RIGHT_FG,
        ):
            super().__init__(parent)
            self.remove_style_all()
            self.set_size(420, lv.SIZE.CONTENT)
            self.add_style(
                StyleWrapper()
                .bg_color(lv_theme.CONT_ITEM_BG)
                .bg_opa()
                .radius(0)
                .border_width(0)
                .pad_hor(6)
                .pad_ver(20)
                .text_font(font_GeistRegular20)
                .text_letter_space(-1)
                .text_align_left(),
                0,
            )
            self.label_left = lv.label(self)
            # self.label_left.set_recolor(True)
            self.label_left.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
            self.label_left.set_long_mode(lv.label.LONG.WRAP)
            self.label_left.set_text(left_text)
            self.label_left.add_style(
                StyleWrapper()
                .text_color(lv_theme.CONT_ITEM_FG)
                .align(lv.ALIGN.TOP_LEFT),
                0,
            )
            if right_text:
                self.label_right = lv.label(self)
                self.label_right.set_size(lv.SIZE.CONTENT, lv.SIZE.CONTENT)
                # self.label_right.set_recolor(True)
                self.label_right.set_text(right_text)
                self.label_right.add_style(
                    StyleWrapper().text_color(right_text_color), 0
                )
                self.label_right.align(lv.ALIGN.TOP_LEFT, 152, 0)
            if icon_path:
                self.img = lv.img(self)
                self.img.remove_style_all()
                self.img.set_src(icon_path)
                if right_text:
                    self.img.align_to(self.label_right, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 20)
                else:
                    self.img.align(lv.ALIGN.TOP_LEFT, 152, 0)

    def __init__(self):
        super().__init__(
            _(i18n_keys.CONTENT__CERTIFICATIONS),
            None,
        )
        self.add_nav_back()
        self.container = ContainerFlexCol(
            self.content_area,
            self.title,
            padding_row=0,
            pos=(0, 30),
            align=lv.ALIGN.OUT_BOTTOM_LEFT,
        )
        self.container.add_style(StyleWrapper().bg_color(lv_theme.CONT_BG).bg_opa(), 0)
        self.certs_info = [
            ("Model", "UKey Core 26", None, lv_theme.CONT_ITEM_FG),
            (
                "United States",
                "FCC ID: 2BB8VP1",
                theme_path_default("tools_cert-fcc.png"),
                lv_theme.CONT_ITEM_FG,
            ),
            (
                "Europe",
                None,
                theme_path_default("tools_cert-ce.png"),
                lv_theme.CONT_ITEM_FG,
            ),
            (
                "Japan",
                "MIC: 211-240720",
                theme_path_default("tools_cert-mic.png"),
                lv_theme.CONT_ITEM_FG,
            ),
            (
                "Brazil",
                "ANATEL ID: 02335-25-16343",
                theme_path_default("tools_cert-anatel.png"),
                lv_theme.CONT_ITEM_FG,
            ),
        ]
        for i, (country, cert_id, icon_path, color) in enumerate(self.certs_info):
            self.CertificationItem(self.container, country, cert_id, icon_path, color)
            if i != len(self.certs_info) - 1:
                self.line = Line(self.container, 420)
                # self.line.align_to(self, lv.ALIGN.BOTTOM_MID, 0, 0)
                # self.line = lv.line(self.container)
                # self.line.set_size(420, 1)
                # self.line.add_style(
                #     StyleWrapper()
                #     .bg_color(lv_theme.CONT_ITEM_BLINE)
                #     .bg_opa()
                #     .border_opa(lv.OPA.TRANSP)
                #     .border_width(0)
                #     .border_color(lv_theme.CONT_ITEM_BLINE)
                #     , 0
                # )
        self.add_event_cb(self.on_nav_back, lv.EVENT.CLICKED, None)
        self.add_event_cb(self.on_nav_back, lv.EVENT.GESTURE, None)

        # self.content_area.set_style_min_height(660, 0)
        # self.update_btn_layout()
        # if hasattr(self, "bnt_container") and self.bnt_container:
        #     self.bnt_container.align_to(self.content_area, lv.ALIGN.OUT_BOTTOM_MID, 0, 15)

    def on_nav_back(self, event_obj):
        code = event_obj.code
        target = event_obj.get_target()
        if code == lv.EVENT.CLICKED:
            if target == self.nav_back.nav_btn:
                self.destroy(50)
        elif code == lv.EVENT.GESTURE:
            _dir = lv.indev_get_act().get_gesture_dir()
            if _dir == lv.DIR.RIGHT:
                lv.event_send(self.nav_back.nav_btn, lv.EVENT.CLICKED, None)
