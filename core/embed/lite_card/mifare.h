#ifndef _MIFARE_H_
#define _MIFARE_H_

#include <stdint.h>

int read_mnemonic(uint8_t* buffer, uint16_t* out_len);
int write_mnemonic(const uint8_t* buffer, uint8_t buffer_len);
int has_mnemonic(uint8_t* has_data);
int password_to_aes_key(const char* password, uint8_t* aes_key);
int aes_authenticate(const uint8_t* key, uint8_t key_no);
int set_aes_key(const uint8_t* key, uint8_t mode);
uint8_t set_remaining_retry(uint8_t retry);
uint8_t get_remaining_retry(uint8_t* retry);
uint8_t remaining_retry_decrement(void);
uint8_t reset_remaining_retry(void);
uint8_t set_new_tag(uint8_t tag);
uint8_t is_card_new(uint8_t* is_new);
int get_model(int* model);
void mifare_clear_session(void);

#endif  // _MIFARE_H_
