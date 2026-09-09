#ifndef _FACTORY_KEYS_H_
#define _FACTORY_KEYS_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define FACTORY_AUTH_PUBLIC_KEY_SIZE 32U

bool factory_auth_get_public_key(uint32_t key_id, const uint8_t **public_key);

#endif  // _FACTORY_KEYS_H_
