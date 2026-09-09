from trezorio import nfc

from trezor import loop, utils
from trezor.crypto import bip39

from ..i18n import gettext as _, keys as i18n_keys
from . import lv, theme_path, theme_path_default
from .common import FullSizeWindow

LITE_CARD_ERROR_REPONSE = -1
LITE_CARD_SUCCESS_REPONSE = 0
LITE_CARD_ERROR = 1
LITE_CARD_FIND = 2
LITE_CARD_CONNECT_FAILURE = 3
LITE_CARD_NOT_SAME = 4
LITE_CARD_HAS_BEEN_RESET = 5
LITE_CARD_PIN_ERROR = 6
LITE_CARD_NO_BACKUP = 8
LITE_CARD_UNSUPPORTED_WORD_COUNT = 9
LITE_CARD_BLANK = 10
LITE_CARD_WITH_DATA = 11
LITE_CARD_RETRY_DECREMENT_FAILURE = 12
LITE_CARD_RETRY_RESET_FAILURE = 13
LITE_CARD_READ_FAILURE = 14
LITE_CARD_WRITE_FAILURE = 15
LITE_CARD_SET_PIN_FAILURE = 16
LITE_CARD_DISCONNECT = 99
LITE_CARD_OPERATE_SUCCESS = 2
LITE_CARD_SUCCESS_STATUS = b"\x90\x00"
LITE_CARD_DISCONECT_STATUS = b"\x99\x99"

CMD_GET_SERIAL_NUMBER = b"\x80\xcb\x80\x00\x05\xdf\xff\x02\x81\x01"
CMD_OLD_APPLET = b"\x00\xa4\x04\x00\x08\xD1\x56\x00\x01\x32\x83\x40\x01"
# CMD_NEW_APPLET = (
#     b"\x00\xa4\x04\x00\x0E\x6F\x6E\x65\x6B\x65\x79\x2E\x62\x61\x63\x6B\x75\x70\x01"
# )
CMD_GET_PIN_RETRY_COUNT = b"\x80\xcb\x80\x00\x05\xdf\xff\x02\x81\x02"
CMD_RESET_CARD = b"\x80\xcb\x80\x00\x05\xdf\xfe\x02\x82\x05"
CMD_GET_PIN_STATUS = b"\x80\xcb\x80\x00\x05\xdf\xff\x02\x81\x05"
CMD_SELECT_PRIMARY_SAFETY = b"\x00\xa4\x04\x00"
CMD_EXPORT_DATA = b"\x80\x4b\x00\x00"
CMD_BACKUP_DATA = b"\x80\x3b\x00\x00"
CMD_SETUP_NEW_PIN = b"\x80\xcb\x80\x00\x0e\xdf\xfe\x0b\x82\x04\x08\x00\x06"
CMD_GET_BACKUP_STATUS = b"\x80\x6A\x00\x00"
CMD_VERIFY_PIN = b"\x80\x20\x00\x00\x07\x06"


async def handle_sw1sw2_connect_error(self):
    self.channel.publish(LITE_CARD_CONNECT_FAILURE)
    await loop.sleep(180)
    self.clean()
    self.destroy()


async def handle_cleanup(self, data):
    self.channel.publish(data)
    await loop.sleep(180)
    self.clean()
    self.destroy()


async def run_card_search(self):
    from trezor import motor

    while self.searching:
        await loop.sleep(1000)
        if not self.searching:
            return
        if nfc.poll_card():
            motor.vibrate(motor.HEAVY)
            self.searching = False
            self.channel.publish(LITE_CARD_FIND)
            self.clean()
            self.destroy()
            return


async def get_card_num(self):
    card_num = None
    card_num, sw1sw2 = nfc.send_recv(CMD_GET_SERIAL_NUMBER)
    if sw1sw2 == LITE_CARD_DISCONECT_STATUS:
        await handle_sw1sw2_connect_error(self)
        return card_num, LITE_CARD_ERROR_REPONSE
    elif sw1sw2 == LITE_CARD_SUCCESS_STATUS:
        pass
    else:
        _, sw1sw2 = nfc.send_recv(CMD_SELECT_PRIMARY_SAFETY)
        if sw1sw2 == LITE_CARD_DISCONECT_STATUS:
            await handle_sw1sw2_connect_error(self)
            return card_num, LITE_CARD_ERROR_REPONSE
        card_num, sw1sw2 = nfc.send_recv(CMD_GET_SERIAL_NUMBER)
        if sw1sw2 == LITE_CARD_DISCONECT_STATUS:
            await handle_sw1sw2_connect_error(self)
            return card_num, LITE_CARD_ERROR_REPONSE

    if isinstance(card_num, bytes):
        card_num_str = card_num.decode("utf-8")
    else:
        card_num_str = str(card_num)

    return card_num_str, LITE_CARD_SUCCESS_REPONSE


def get_card_type(card_num_str):
    card_type = None
    if len(card_num_str) >= 5:
        if card_num_str[4] == "T" and card_num_str[5] == "2":
            card_type = "OLD"
        elif card_num_str[4] == "B" and card_num_str[5] == "A":
            card_type = "NEW"
    return card_type


async def check_card_data(self):
    card_num, status = await get_card_num(self)
    if status == LITE_CARD_ERROR_REPONSE:
        return
    pinresp, pinsw1sw2 = nfc.send_recv(CMD_GET_PIN_STATUS)
    if pinsw1sw2 == LITE_CARD_DISCONECT_STATUS:
        await handle_sw1sw2_connect_error(self)
        return
    if pinsw1sw2 == LITE_CARD_SUCCESS_STATUS and pinresp == b"\x02":
        if card_num is not None:
            data = "2" + str(card_num)
            await handle_cleanup(self, data)
            return
    elif pinsw1sw2 == LITE_CARD_SUCCESS_STATUS:
        if card_num is not None:
            data = "3" + str(card_num)
            await handle_cleanup(self, data)
            return
    else:
        await handle_cleanup(self, LITE_CARD_ERROR_REPONSE)
        return


async def check_best_try_restcard(self):
    numresp, numsw1sw2 = nfc.send_recv(CMD_GET_PIN_RETRY_COUNT)
    if numsw1sw2 == LITE_CARD_DISCONECT_STATUS:
        await handle_sw1sw2_connect_error(self)
        return LITE_CARD_ERROR_REPONSE

    if numresp in [b"\x01", b"\x00"] and numsw1sw2 == LITE_CARD_SUCCESS_STATUS:

        _, restsw1sw2 = nfc.send_recv(CMD_RESET_CARD, True)
        if restsw1sw2 == LITE_CARD_DISCONECT_STATUS:
            await handle_sw1sw2_connect_error(self)
            return LITE_CARD_ERROR_REPONSE
        await handle_cleanup(self, LITE_CARD_HAS_BEEN_RESET)
        return LITE_CARD_ERROR_REPONSE
    return LITE_CARD_SUCCESS_REPONSE


def _format_retry_status() -> str:
    retry_count = nfc.mifare_get_remaining_retry()
    return f"63C{retry_count:X}"


def _encode_mifare_mnemonic(mnemonic) -> bytes:
    encoder = UkeyMnemonicEncoder()
    if isinstance(mnemonic, bytes):
        mnemonic = mnemonic.decode()
    return encoder.encode_mnemonics(mnemonic)


async def start_prepare_mifare_backup(self, pin):
    nfc.mifare_clear_session()
    try:
        if not nfc.mifare_remaining_retry_decrement():
            if __debug__:
                print("nfc: failed to decrement retry count before prepare")
            await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to decrement retry count before prepare: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
        return

    if not nfc.mifare_authenticate(pin):
        try:
            await handle_cleanup(self, _format_retry_status())
        except RuntimeError as exc:
            if __debug__:
                print(f"nfc: retry status unavailable after prepare auth: {exc}")
            await handle_cleanup(self, LITE_CARD_PIN_ERROR)
        return

    try:
        if not nfc.mifare_reset_remaining_retry():
            if __debug__:
                print("nfc: failed to reset retry count after prepare auth")
            await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to reset retry count after prepare auth: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
        return

    try:
        has_data = nfc.mifare_has_mnemonic()
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to check mnemonic before backup: {exc}")
        await handle_cleanup(self, LITE_CARD_READ_FAILURE)
        return

    await handle_cleanup(self, LITE_CARD_WITH_DATA if has_data else LITE_CARD_BLANK)


async def start_write_mifare_backup(self, pin, mnemonic, new_pin):
    if not new_pin:
        if __debug__:
            print("nfc: missing new PIN for backup")
        await handle_cleanup(self, LITE_CARD_SET_PIN_FAILURE)
        return

    nfc.mifare_clear_session()
    try:
        if not nfc.mifare_remaining_retry_decrement():
            if __debug__:
                print("nfc: failed to decrement retry count before backup")
            await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to decrement retry count before backup: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
        return

    if not nfc.mifare_authenticate(pin):
        try:
            await handle_cleanup(self, _format_retry_status())
        except RuntimeError as exc:
            if __debug__:
                print(f"nfc: retry status unavailable after backup auth: {exc}")
            await handle_cleanup(self, LITE_CARD_PIN_ERROR)
        return

    try:
        if not nfc.mifare_reset_remaining_retry():
            if __debug__:
                print("nfc: failed to reset retry count after backup auth")
            await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to reset retry count after backup auth: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
        return

    try:
        if not nfc.mifare_write_mnemonic(_encode_mifare_mnemonic(mnemonic)):
            if __debug__:
                print("nfc: failed to write mnemonic")
            await handle_cleanup(self, LITE_CARD_WRITE_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to write mnemonic: {exc}")
        await handle_cleanup(self, LITE_CARD_WRITE_FAILURE)
        return

    try:
        if not nfc.mifare_set_new_tag(1):
            if __debug__:
                print("nfc: failed to mark backup card as initialized")
            await handle_cleanup(self, LITE_CARD_WRITE_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to mark backup card as initialized: {exc}")
        await handle_cleanup(self, LITE_CARD_WRITE_FAILURE)
        return

    try:
        if new_pin != pin and not nfc.mifare_set_pin(new_pin):
            if __debug__:
                print("nfc: failed to set backup card PIN")
            await handle_cleanup(self, LITE_CARD_SET_PIN_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to set backup card PIN: {exc}")
        await handle_cleanup(self, LITE_CARD_SET_PIN_FAILURE)
        return

    await handle_cleanup(self, LITE_CARD_OPERATE_SUCCESS)


async def start_import_mifare_backup(self, pin):
    nfc.mifare_clear_session()
    try:
        if not nfc.mifare_remaining_retry_decrement():
            if __debug__:
                print("nfc: failed to decrement retry count before import")
            await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to decrement retry count before import: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_DECREMENT_FAILURE)
        return

    if not nfc.mifare_authenticate(pin):
        try:
            await handle_cleanup(self, _format_retry_status())
        except RuntimeError as exc:
            if __debug__:
                print(f"nfc: retry status unavailable after import auth: {exc}")
            await handle_cleanup(self, LITE_CARD_PIN_ERROR)
        return

    try:
        if not nfc.mifare_reset_remaining_retry():
            if __debug__:
                print("nfc: failed to reset retry count after import auth")
            await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to reset retry count after import auth: {exc}")
        await handle_cleanup(self, LITE_CARD_RETRY_RESET_FAILURE)
        return

    try:
        if not nfc.mifare_has_mnemonic():
            await handle_cleanup(self, LITE_CARD_NO_BACKUP)
            return
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to check mnemonic before import: {exc}")
        await handle_cleanup(self, LITE_CARD_READ_FAILURE)
        return

    try:
        exportresp = nfc.mifare_read_mnemonic()
    except RuntimeError as exc:
        if __debug__:
            print(f"nfc: failed to read mnemonic: {exc}")
        await handle_cleanup(self, LITE_CARD_READ_FAILURE)
        return

    decoder = UkeyMnemonicEncoder()
    decoded_mnemonics = decoder.decode_mnemonics(exportresp)
    if decoded_mnemonics == "":
        await handle_cleanup(self, LITE_CARD_NO_BACKUP)
        return

    word_count = len(decoded_mnemonics.split())
    if word_count in [15, 21]:
        await handle_cleanup(self, LITE_CARD_UNSUPPORTED_WORD_COUNT)
        return

    await handle_cleanup(self, decoded_mnemonics)


class MnemonicEncoder:
    def encode_mnemonics(self, seed):
        n = 2048
        words = seed.split()
        i = 0
        while words:
            w = words.pop()
            k = bip39.find(w)
            i = i * n + k
        result_str = str(i)
        if len(result_str) % 2 != 0:
            result_str = "0" + result_str
        return result_str

    def int_to_hex_str(self, num):
        """Convert an integer to a hexadecimal string."""
        hex_str = hex(num)[2:]  # Convert to hex and remove the '0x' prefix
        if len(hex_str) % 2:  # Make sure the length is even
            hex_str = "0" + hex_str
        return hex_str

    def fromhex(self, hex_str):
        """Convert a hex string to a byte array."""
        return bytes(int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2))

    def bytes_to_hex_str(self, byte_data):
        return "".join(f"{byte:02x}" for byte in byte_data)

    def decode_mnemonics(self, encoded_mnemonic_str):
        n = 2048
        encoded_int = int(encoded_mnemonic_str, 10)
        words = []

        while encoded_int > 0:
            index = int(encoded_int % n)
            encoded_int = encoded_int // n
            words.append(bip39.get_word(index))
        # v1 fix
        fix_fill_count = 0
        supported_mnemonic_length = [12, 15, 18, 21, 24]
        for length in supported_mnemonic_length:
            if len(words) == length:
                break
            if len(words) < length:
                fix_fill_count = length - len(words)
                break
        words.extend([bip39.get_word(0)] * fix_fill_count)

        return " ".join(words)

    def parse_card_data(self, data):

        encoded_mnemonic_bytes = data[:-4]
        version_bytes = data[-4:-3]
        lang_bytes = data[-3:-2]
        encoded_mnemonic_str = self.bytes_to_hex_str(encoded_mnemonic_bytes)
        version = self.bytes_to_hex_str(version_bytes)
        lang = self.bytes_to_hex_str(lang_bytes)

        return encoded_mnemonic_str, version, lang


class UkeyMnemonicEncoder:
    def crc16(self, data: bytes):
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _bit in range(8):
                if (crc & 0x0001) != 0:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    def encode_mnemonics(self, seed):
        ENT_BYTES_TO_CHECK_BITS_LENGTH = {16: 4, 20: 5, 24: 6, 28: 7, 32: 8}
        ENT_BYTES_TO_TYPE = {16: 1, 20: 2, 24: 3, 28: 4, 32: 5}
        words = seed.split()
        words_len = len(words)
        i = 0
        for w in words:
            k = bip39.find(w)
            i = (i << 11) | k

        bit_len = words_len * 11  # mnemonics bit length
        ent_bit_len = bit_len * 32 // 33
        byte_len = ent_bit_len // 8  # entropy byte length
        check_bit_len = ENT_BYTES_TO_CHECK_BITS_LENGTH[byte_len]  # checksum bit length

        i >>= check_bit_len  # remove checksum bits

        out = bytearray(byte_len)
        x = i
        for j in range(byte_len - 1, -1, -1):
            out[j] = x & 0xFF
            x >>= 8

        type = bytes([ENT_BYTES_TO_TYPE[byte_len]])
        crc = self.crc16(bytes([ENT_BYTES_TO_TYPE[byte_len]]) + out)

        encode_mnemonics_data = type + out + crc
        return encode_mnemonics_data

    def decode_mnemonics(self, encoded_mnemonic):
        TYPE_TO_ENT_BYTES = {1: 16, 2: 20, 3: 24, 4: 28, 5: 32}
        ent_byte_len = len(encoded_mnemonic) - 3

        type = encoded_mnemonic[0]
        ent_byte = encoded_mnemonic[1:-2]
        crc = encoded_mnemonic[-2:]

        if ent_byte_len != TYPE_TO_ENT_BYTES[type]:
            return ""

        if self.crc16(encoded_mnemonic[:-2]) != crc:
            return ""

        return bip39.from_data(ent_byte)


class SearchDeviceScreen(FullSizeWindow):
    def __init__(self):
        is_lite = utils.get_current_backup_type() == utils.BACKUP_METHOD_LITE
        super().__init__(
            _(i18n_keys.TITLE__CONNECTING),
            _(
                i18n_keys.CONTENT__KEEP_LITE_DEVICE_TOGETHER_BACKUP_COMPLETE
                if is_lite
                else i18n_keys.SUBTITLE__RING_NFC_CONNECTING
            ),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            anim_dir=0,
        )

        self.content_area.set_height(600)
        self.img_searching = lv.gif(self.content_area)
        self.img_searching.set_src(theme_path("nfc-searching.gif"))
        # print(theme_path("tools/nfc-searching.gif"))
        self.img_searching.align(lv.ALIGN.CENTER, 0, 0)
        # self.img_searching.set_src(theme_path_png("nfc-icon-searching"))
        # self.img_searching.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 175)
        # is_load_icon = False
        # for i in range(100000):
        #     lv.timer_handler()
        #     w = self.img_searching.get_width()
        #     if w > 0:
        #         is_load_icon = True
        #         break
        # w = self.img_searching.get_width()
        # h = self.img_searching.get_height()
        # center_x = self.img_searching.get_x_aligned()+int(w/2)
        # center_y = self.img_searching.get_y_aligned()+int(h/2)
        # self.circle_diameters = [301, 245, 181]
        # self.circle_colors = [
        #     LV_COLOR_MAKE(0xF9, 0xF9, 0xF9),
        #     LV_COLOR_MAKE(0xEE, 0xEE, 0xEE),
        #     LV_COLOR_MAKE(0xB8, 0xB8, 0xB8)
        # ]
        # self.circle_colors = [
        #     LV_COLOR_MAKE(0xFE, 0xFE, 0xFE),
        #     LV_COLOR_MAKE(0xF4, 0xF4, 0xF4),
        #     LV_COLOR_MAKE(0xDC, 0xDC, 0xDC),
        # ]
        # self.circle_border_widths = [6, 4, 2]
        # self.circles = []
        # for i, d in enumerate(self.circle_diameters):
        #     circle = lv.obj(self.content_area)
        #     circle.remove_style_all()
        #     circle.set_size(d, d)
        #     circle.set_pos(int(center_x - d/2), int(center_y - d/2))
        #     circle.add_style(
        #         StyleWrapper()
        #         .radius(lv.RADIUS.CIRCLE)
        #         .bg_opa(lv.OPA.TRANSP)
        #         .border_color(self.circle_colors[i])
        #         .border_width(self.circle_border_widths[i]),
        #         0
        #     )
        #     circle.add_flag(lv.obj.FLAG.HIDDEN)
        #     self.circles.append(circle)

        # self.anim = lv.anim_t()
        # self.anim.init()
        # self.anim.set_values(0, len(self.circles))
        # self.anim.set_time(1000)
        # self.anim.set_repeat_count(0xFFFF)  # infinite
        # self.anim.set_path_cb(lv.anim_t.path_linear)
        # self.anim.set_custom_exec_cb(lambda _a, val: self.set_status(val))
        # self.anim_r = lv.anim_t.start(self.anim)
        self.searching = True
        loop.schedule(run_card_search(self))

    def show_dismiss_anim(self):
        self.searching = False
        super().show_dismiss_anim()

    def destroy(self, delay_ms=400):
        self.searching = False
        super().destroy(delay_ms)

    def set_status(self, status):
        try:
            if status < len(self.circles):
                self.circles[len(self.circles) - status - 1].clear_flag(
                    lv.obj.FLAG.HIDDEN
                )
            else:
                for c in self.circles:
                    c.add_flag(lv.obj.FLAG.HIDDEN)
        except Exception:
            lv.anim_del(self.anim_r.var, None)


class TransferDataScreen(FullSizeWindow):
    def __init__(self):
        super().__init__(
            _(i18n_keys.TITLE__TRANSFERRING),
            _(i18n_keys.TITLE__TRANSFERRING_DESC),
            cancel_text=_(i18n_keys.BUTTON__CANCEL),
            anim_dir=0,
        )
        self.img_searching = lv.img(self.content_area)
        self.img_searching.set_src(theme_path_default("tools_nfc-icon-transfering.png"))
        self.img_searching.align_to(self.subtitle, lv.ALIGN.OUT_BOTTOM_MID, 0, 237)
        self.searching = True

    def set_angle(self, angle):
        try:
            self.img_bg.set_angle(angle)
        except Exception:
            pass

    def check_card_data(self):
        loop.schedule(check_card_data(self))

    def stop_animation(self):
        self.searching = False

    def prepare_mifare_backup(self, pin):
        loop.schedule(start_prepare_mifare_backup(self, pin))

    def write_mifare_backup(self, pin, mnemonics, new_pin):
        loop.schedule(start_write_mifare_backup(self, pin, mnemonics, new_pin))

    def import_mifare_backup(self, pin):
        loop.schedule(start_import_mifare_backup(self, pin))
