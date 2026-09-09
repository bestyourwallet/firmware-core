from typing import *


# extmod/modtrezorio/modtrezorio-nfc.h
def pwr_ctrl(on_off: bool) -> bool:
    """
    Control NFC power.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def poll_card() -> bool:
    """
    Poll card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def send_recv(apdu: bytes, safe: bool = False) -> tuple[bytes, bytes]:
    """
    Send receive data through NFC.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_authenticate(pin: str) -> bool:
    """
    authenticate from Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_read_mnemonic() -> bytes:
    """
    Read mnemonic from Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_write_mnemonic(data: bytes) -> bool:
    """
    Write mnemonic to Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_has_mnemonic() -> bool:
    """
    Return whether the Mifare card contains a valid mnemonic payload.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_get_model() -> int:
    """
    Return the Mifare device model.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_get_remaining_retry() -> int:
    """
    Return the external retry counter stored on the Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_remaining_retry_decrement() -> bool:
    """
    Decrement the external retry counter stored on the Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_reset_remaining_retry() -> bool:
    """
    Reset the external retry counter stored on the Mifare card.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_set_new_tag(tag: int) -> bool:
    """
    Write the new-card tag byte to the public page.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_is_card_new() -> bool:
    """
    Return whether the card is considered new (tag == 0x00).
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_set_pin(pin: str) -> bool:
    """
    Set the Mifare card AES password from the given 6-digit pin.
    """


# extmod/modtrezorio/modtrezorio-nfc.h
def mifare_clear_session() -> None:
    """
    Clear the current Mifare authentication session.
    """
