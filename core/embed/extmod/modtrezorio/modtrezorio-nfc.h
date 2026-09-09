
#include "embed/extmod/trezorobj.h"

#include "lite_card.h"
#include "mifare.h"
#include "nfc.h"

/// package: trezorio.nfc
STATIC bool mifare_pin_to_key(mp_obj_t pin_obj, uint8_t *aes_key);

/// def pwr_ctrl(on_off: bool) -> bool:
///     """
///     Control NFC power.
///     """
STATIC mp_obj_t mod_trezorio_NFC_pwr_ctrl(mp_obj_t on_off) {
  return nfc_pwr_ctl(mp_obj_is_true(on_off)) ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_trezorio_NFC_pwr_ctrl_obj,
                                 mod_trezorio_NFC_pwr_ctrl);

/// def poll_card() -> bool:
///     """
///     Poll card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_poll_card(void) {
  return nfc_poll_card() ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_poll_card_obj,
                                 mod_trezorio_NFC_poll_card);

/// def send_recv(apdu: bytes, safe: bool = False) -> tuple[bytes, bytes]:
///     """
///     Send receive data through NFC.
///     """
STATIC mp_obj_t mod_trezorio_NFC_send_recv(size_t n_args,
                                           const mp_obj_t *args) {
  bool safe = n_args > 1 && args[1] == mp_const_true;
  mp_buffer_info_t apdu = {0};
  mp_get_buffer_raise(args[0], &apdu, MP_BUFFER_READ);

  if (apdu.len > 255) {
    mp_raise_msg(&mp_type_ValueError, "APDU too long");
  }

  uint8_t sw1sw2[2] = {0};
  uint8_t resp[256] = {0};
  uint16_t resp_len = sizeof(resp);

  bool success = lite_card_apdu((uint8_t *)apdu.buf, apdu.len, resp, &resp_len,
                                sw1sw2, safe);

  mp_obj_tuple_t *tuple = MP_OBJ_TO_PTR(mp_obj_new_tuple(2, NULL));

  tuple->items[0] = mp_obj_new_str_copy(&mp_type_bytes, resp, resp_len);

  if (!success) {
    sw1sw2[0] = 0x99;
    sw1sw2[1] = 0x99;
  }

  tuple->items[1] = mp_obj_new_str_copy(&mp_type_bytes, sw1sw2, 2);

  return MP_OBJ_FROM_PTR(tuple);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mod_trezorio_NFC_send_recv_obj, 1, 2,
                                           mod_trezorio_NFC_send_recv);

/// def mifare_authenticate(pin: str) -> bool:
///     """
///     authenticate from Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_authenticate(mp_obj_t pin_obj) {
  uint8_t aes_key[16] = {0};
  mifare_pin_to_key(pin_obj, aes_key);

  if (aes_authenticate(aes_key, 0) != true) {
    printf("aes_authenticate fail\n");
    return mp_const_false;
  }

  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_trezorio_NFC_mifare_authenticate_obj,
                                 mod_trezorio_NFC_mifare_authenticate);

STATIC bool mifare_pin_to_key(mp_obj_t pin_obj, uint8_t *aes_key) {
  if (!mp_obj_is_str(pin_obj)) {
    mp_raise_TypeError(MP_ERROR_TEXT("pin must be str"));
  }

  size_t pin_len = 0;
  const char *pin_bytes = (const char *)mp_obj_str_get_data(pin_obj, &pin_len);

  if (pin_len != 6) {
    mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("pin len failed"));
  }

  uint8_t pin[7] = {0};
  memcpy(pin, pin_bytes, pin_len);
  pin[pin_len] = '\0';
  password_to_aes_key((const char *)pin, aes_key);
  return true;
}

/// def mifare_read_mnemonic() -> bytes:
///     """
///     Read mnemonic from Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_read_mnemonic(void) {
  uint8_t buffer[256] = {0};
  uint16_t buffer_len = 0;

  if (read_mnemonic(buffer, &buffer_len) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to read mnemonic");
  }

  if (buffer_len > 140) {
    mp_raise_msg(&mp_type_ValueError, "Mnemonic too long");
  }
  return mp_obj_new_bytes(buffer, buffer_len);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_mifare_read_mnemonic_obj,
                                 mod_trezorio_NFC_mifare_read_mnemonic);

/// def mifare_write_mnemonic(data: bytes) -> bool:
///     """
///     Write mnemonic to Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_write_mnemonic(mp_obj_t data) {
  mp_buffer_info_t data_buf = {0};
  mp_get_buffer_raise(data, &data_buf, MP_BUFFER_READ);
  if (data_buf.len == 0 || data_buf.len > 140) {
    mp_raise_msg(&mp_type_ValueError, "Invalid data length");
  }
  if (write_mnemonic(data_buf.buf, data_buf.len) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to write mnemonic");
  }
  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_trezorio_NFC_mifare_write_mnemonic_obj,
                                 mod_trezorio_NFC_mifare_write_mnemonic);

/// def mifare_has_mnemonic() -> bool:
///     """
///     Return whether the Mifare card contains a valid mnemonic payload.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_has_mnemonic(void) {
  uint8_t has_data = false;

  if (has_mnemonic(&has_data) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to inspect mnemonic");
  }

  return has_data ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_mifare_has_mnemonic_obj,
                                 mod_trezorio_NFC_mifare_has_mnemonic);

/// def mifare_get_model() -> int:
///     """
///     Return the Mifare device model.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_get_model(void) {
  int model = 0;

  if (get_model(&model) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to read Mifare model");
  }

  return mp_obj_new_int(model);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_mifare_get_model_obj,
                                 mod_trezorio_NFC_mifare_get_model);

/// def mifare_get_remaining_retry() -> int:
///     """
///     Return the external retry counter stored on the Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_get_remaining_retry(void) {
  uint8_t retry = 0;

  if (get_remaining_retry(&retry) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to read remaining retry");
  }

  return mp_obj_new_int(retry);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(
    mod_trezorio_NFC_mifare_get_remaining_retry_obj,
    mod_trezorio_NFC_mifare_get_remaining_retry);

/// def mifare_remaining_retry_decrement() -> bool:
///     """
///     Decrement the external retry counter stored on the Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_remaining_retry_decrement(void) {
  if (remaining_retry_decrement() != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to decrement remaining retry");
  }

  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(
    mod_trezorio_NFC_mifare_remaining_retry_decrement_obj,
    mod_trezorio_NFC_mifare_remaining_retry_decrement);

/// def mifare_reset_remaining_retry() -> bool:
///     """
///     Reset the external retry counter stored on the Mifare card.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_reset_remaining_retry(void) {
  if (reset_remaining_retry() != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to reset remaining retry");
  }

  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(
    mod_trezorio_NFC_mifare_reset_remaining_retry_obj,
    mod_trezorio_NFC_mifare_reset_remaining_retry);

/// def mifare_set_new_tag(tag: int) -> bool:
///     """
///     Write the new-card tag byte to the public page.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_set_new_tag(mp_obj_t tag_obj) {
  if (!mp_obj_is_int(tag_obj)) {
    mp_raise_TypeError(MP_ERROR_TEXT("tag must be int"));
  }
  int tag = mp_obj_get_int(tag_obj) & 0xFF;
  if (set_new_tag((uint8_t)tag) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to write new tag");
  }
  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_trezorio_NFC_mifare_set_new_tag_obj,
                                 mod_trezorio_NFC_mifare_set_new_tag);

/// def mifare_is_card_new() -> bool:
///     """
///     Return whether the card is considered new (tag == 0x00).
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_is_card_new(void) {
  uint8_t is_new = 0;

  if (is_card_new(&is_new) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to read new-card flag");
  }

  return is_new ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_mifare_is_card_new_obj,
                                 mod_trezorio_NFC_mifare_is_card_new);

/// def mifare_set_pin(pin: str) -> bool:
///     """
///     Set the Mifare card AES password from the given 6-digit pin.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_set_pin(mp_obj_t pin_obj) {
  uint8_t aes_key[16] = {0};
  mifare_pin_to_key(pin_obj, aes_key);

  if (set_aes_key(aes_key, 0) != true) {
    mp_raise_msg(&mp_type_RuntimeError, "Failed to set Mifare pin");
  }

  return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_trezorio_NFC_mifare_set_pin_obj,
                                 mod_trezorio_NFC_mifare_set_pin);
/// def mifare_clear_session() -> None:
///     """
///     Clear the current Mifare authentication session.
///     """
STATIC mp_obj_t mod_trezorio_NFC_mifare_clear_session(void) {
  mifare_clear_session();
  return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mod_trezorio_NFC_mifare_clear_session_obj,
                                 mod_trezorio_NFC_mifare_clear_session);

STATIC const mp_rom_map_elem_t mod_trezorio_NFC_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_nfc)},
    {MP_ROM_QSTR(MP_QSTR_pwr_ctrl), MP_ROM_PTR(&mod_trezorio_NFC_pwr_ctrl_obj)},
    {MP_ROM_QSTR(MP_QSTR_poll_card),
     MP_ROM_PTR(&mod_trezorio_NFC_poll_card_obj)},
    {MP_ROM_QSTR(MP_QSTR_send_recv),
     MP_ROM_PTR(&mod_trezorio_NFC_send_recv_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_authenticate),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_authenticate_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_read_mnemonic),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_read_mnemonic_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_write_mnemonic),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_write_mnemonic_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_has_mnemonic),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_has_mnemonic_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_get_model),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_get_model_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_get_remaining_retry),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_get_remaining_retry_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_remaining_retry_decrement),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_remaining_retry_decrement_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_reset_remaining_retry),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_reset_remaining_retry_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_set_new_tag),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_set_new_tag_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_is_card_new),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_is_card_new_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_set_pin),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_set_pin_obj)},
    {MP_ROM_QSTR(MP_QSTR_mifare_clear_session),
     MP_ROM_PTR(&mod_trezorio_NFC_mifare_clear_session_obj)},
};

STATIC MP_DEFINE_CONST_DICT(mod_trezorio_NFC_globals,
                            mod_trezorio_NFC_globals_table);

STATIC const mp_obj_module_t mod_trezorio_NFC_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&mod_trezorio_NFC_globals,
};
