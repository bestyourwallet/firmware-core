#include "factory_keys.h"

#if PRODUCTION

/*
 * Production factory authorization public key. The corresponding private key
 * must not be stored in this repository or on a factory workstation.
 */
#define FACTORY_AUTH_PRODUCTION_KEY_CONFIGURED 1
static const uint8_t factory_auth_key_0[FACTORY_AUTH_PUBLIC_KEY_SIZE] = {
    0xb0, 0xff, 0x06, 0xac, 0xb1, 0x14, 0x19, 0xf5, 0x65, 0x15, 0x41,
    0xcf, 0xdf, 0x23, 0x95, 0x2d, 0xad, 0xdf, 0xaf, 0x4a, 0xae, 0x12,
    0x95, 0xf8, 0x19, 0xa3, 0x66, 0x10, 0xa3, 0x29, 0x0e, 0x58,
};

#else

/* RFC 8032 test vector public key. Its private key is public; development only.
 */
#define FACTORY_AUTH_PRODUCTION_KEY_CONFIGURED 1
static const uint8_t factory_auth_key_0[FACTORY_AUTH_PUBLIC_KEY_SIZE] = {
    0xd7, 0x5a, 0x98, 0x01, 0x82, 0xb1, 0x0a, 0xb7, 0xd5, 0x4b, 0xfe,
    0xd3, 0xc9, 0x64, 0x07, 0x3a, 0x0e, 0xe1, 0x72, 0xf3, 0xda, 0xa6,
    0x23, 0x25, 0xaf, 0x02, 0x1a, 0x68, 0xf7, 0x07, 0x51, 0x1a,
};

#endif

static const uint8_t *const factory_auth_keys[] = {
    factory_auth_key_0,
};

bool factory_auth_get_public_key(uint32_t key_id, const uint8_t **public_key) {
  if (!FACTORY_AUTH_PRODUCTION_KEY_CONFIGURED || public_key == NULL ||
      key_id >= (sizeof(factory_auth_keys) / sizeof(factory_auth_keys[0]))) {
    return false;
  }

  *public_key = factory_auth_keys[key_id];
  return true;
}
