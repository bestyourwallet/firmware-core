#include STM32_HAL_H

#include "se_boot.h"
#include "common.h"
#include "rand.h"
#include "se.h"

// clang-format off
#define SE_BOOT_REQUEST_PORT    GPIOF
#define SE_BOOT_REQUEST_PIN     GPIO_PIN_7

#define SE_BOOT_ENTRY_DELAY_MS  1000
#define SE_APP_ENTRY_DELAY_MS   1000
#define SE_STATE_POLL_RETRY     20
#define SE_STATE_POLL_DELAY_MS  100

static uint8_t device_addr = SE_MASTER_ADDRESS;

void se_boot_set_address(uint8_t addr) {
  device_addr = (addr << 1);
}

static void se_boot_request_set(bool enable) {
  HAL_GPIO_WritePin(SE_BOOT_REQUEST_PORT, SE_BOOT_REQUEST_PIN, enable ? GPIO_PIN_RESET : GPIO_PIN_SET);
}

static bool se_wait_state(uint8_t expected_state) {
  uint8_t state = 0;

  for (uint8_t i = 0; i < SE_STATE_POLL_RETRY; i++) {
    if (se_get_state_ex(&state) && state == expected_state) {
      return true;
    }
    hal_delay(SE_STATE_POLL_DELAY_MS);
  }

  return false;
}

static bool _se_get_state(uint8_t addr, uint8_t *state) {
  uint8_t cmd[5] = {0x80, 0xca, 0x00, 00, 0x00};
  uint16_t resp_len = 1;

  if (!se_transmit_ex(addr, cmd, sizeof(cmd), state, &resp_len)) {
    return false;
  }

  if ((resp_len != 0x01) ||
      ((state[0] != 0x00) && (state[0] != 0x55) && (state[0] != 0x33))) {
    return false;
  }
  return true;
}

bool se01_get_state(uint8_t *state) {
  return _se_get_state(SE_1ST_ADDRESS, state);
}

uint8_t se_get_state(void) {
  uint8_t state, boot_flag = 0;
  ensure(_se_get_state(SE_1ST_ADDRESS, &state) ? sectrue : secfalse, "se1 get state failed");
  if (state == SE_STATE_BOOT) {
    boot_flag |= SE_1ST_IN_BOOT;
  }
  return boot_flag;
}

bool se_get_state_ex(uint8_t *state) {
  return _se_get_state(device_addr, state);
}

bool se_get_update_progress(uint8_t *progress) {
  uint8_t cmd[5] = {0x80, 0xFC, 0x00, 0x55, 0x00};
  uint16_t resp_len = 1;

  if (!se_transmit_ex(device_addr, cmd, sizeof(cmd), progress, &resp_len)) {
    return false;
  }

  if (resp_len != 0x01) {
    return false;
  }
  return true;
}

char *se_get_version_ex(void) {
  uint8_t get_ver[5] = {0x00, 0xf7, 0x00, 00, 0x00};
  static char ver[16] = {0};
  uint16_t ver_len = sizeof(ver);

  memset(ver, 0, sizeof(ver));

  if (!se_transmit_ex(device_addr, get_ver, sizeof(get_ver), (uint8_t *)ver, &ver_len)) {
    return NULL;
  }

  return ver;
}

bool se_back_to_boot(void) {
  uint8_t cmd[5] = {0x80, 0xfc, 0x00, 0xff, 0x00};
  uint16_t resp_len = 0;
  if (!se_transmit_ex(device_addr, cmd, sizeof(cmd), NULL, &resp_len)) {
    return false;
  }
  return true;
}

bool se_active_app(void) {
  uint8_t cmd[5] = {0x80, 0xfc, 0x00, 0x04, 0x00};
  uint16_t resp_len = 0;
  if (!se_transmit_ex(device_addr, cmd, sizeof(cmd), NULL, &resp_len)) {
    return false;
  }
  return true;
}

static bool se_reboot_app(void) {
  uint8_t cmd[5] = {0x80, 0xfc, 0x00, 0x05, 0x00};
  uint16_t resp_len = 0;
  if (!se_transmit_ex(device_addr, cmd, sizeof(cmd), NULL, &resp_len)) {
    return false;
  }
  return true;
}

bool se_update(uint8_t step, uint8_t *data, uint16_t data_len) {
  uint8_t cmd[1032];
  uint16_t cmd_len = 5, resp_len = 0;
  cmd[0] = 0x80;
  cmd[1] = 0xFC;
  cmd[2] = 0x00;
  cmd[3] = step;
  cmd[4] = 0x00;

  // send steps
  if (0x01 == step) {
    if (data_len != 1024) {
      return false;
    }
    cmd[5] = 0x04;
    cmd[6] = 0x00;
    memcpy(cmd + 7, data, data_len);
    cmd_len += 2 + data_len;

  } else if (0x02 == step) {
    if (data_len != 512) {
      return false;
    }
    cmd[5] = 0x02;
    cmd[6] = 0x00;
    memcpy(cmd + 7, data, 512);
    cmd_len += 2 + 512;
  }
  if (!se_transmit_ex(device_addr, cmd, cmd_len, NULL, &resp_len)) {
    return false;
  }
  return true;
}

bool se_back_to_boot_progress(void) {
  uint8_t state = 0;
  if (se_get_state_ex(&state) && state == SE_STATE_BOOT) {
    return true;
  }

  se_boot_request_set(true);
  se_back_to_boot();
  se_reset();
  hal_delay(SE_BOOT_ENTRY_DELAY_MS);
  se_boot_request_set(false);

  if (se_wait_state(SE_STATE_BOOT)) {
    return true;
  }

  se_boot_request_set(false);
  return false;
}

bool se_verify_firmware(uint8_t *header, uint32_t header_len) {
  return se_update(1, header, header_len);
}

bool se_check_firmware(void) {
  return se_update(3, NULL, 0);
}

bool se_update_firmware(uint8_t *data, uint32_t data_len, uint8_t percent_start,
                        uint8_t weights, void (*ui_callback)(int progress)) {
  uint32_t offset_len = 0;
  while (data_len) {
    uint32_t packet_len = data_len > 512 ? 512 : data_len;

    if (!se_update(2, data + offset_len, packet_len)) {
      return false;
    }
    data_len -= packet_len;
    offset_len += packet_len;
    if (ui_callback) {
      ui_callback(percent_start +
                  weights * offset_len / (offset_len + data_len));
    }
  }

  return true;
}

bool se_active_app_progress(void) {
  if (!se_active_app()) {
    return false;
  }
  hal_delay(SE_APP_ENTRY_DELAY_MS);

  if (!se_wait_state(SE_STATE_APP)) {
    return false;
  }

  if (!se_reboot_app()) {
    return false;
  }
  hal_delay(SE_BOOT_ENTRY_DELAY_MS);

  return se_wait_state(SE_STATE_APP);
}
