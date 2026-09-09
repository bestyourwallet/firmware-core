#ifndef _SE_BOOT_H_
#define _SE_BOOT_H_

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define SE_STATE_BOOT 0x00
#define SE_STATE_NOT_ACTIVATED 0x33
#define SE_STATE_APP 0x55

#define SE_UPDATE_PARTITION_A 0x01
#define SE_UPDATE_PARTITION_B 0x02

#define SE_FIRMWARE_TYPE_APP_A 0x01  // Firmware Type: APP A
#define SE_FIRMWARE_TYPE_APP_B 0x02  // Firmware Type: APP B

enum {
  SE_1ST_IN_BOOT = 0x01,
};

void se_boot_set_address(uint8_t addr);
uint8_t se_get_state(void);
bool se_get_state_ex(uint8_t* state);
char* se_get_version_ex(void);
bool se_get_update_progress(uint8_t* progress);
bool se_back_to_boot(void);
bool se_active_app(void);
bool se_update(uint8_t step, uint8_t* data, uint16_t data_len);
bool se_back_to_boot_progress(void);
bool se_update_firmware(uint8_t* data, uint32_t data_len, uint8_t percent_start,
                        uint8_t weights, void (*ui_callback)(int progress));
bool se_active_app_progress(void);
bool se_verify_firmware(uint8_t* header, uint32_t header_len);
bool se_check_firmware(void);

bool se01_get_state(uint8_t* state);

#endif
