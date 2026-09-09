#ifndef _FACTORY_AUTH_H_
#define _FACTORY_AUTH_H_

#include <stdbool.h>
#include <stdint.h>

#define FACTORY_AUTH_PROTOCOL_VERSION 1U
#define FACTORY_AUTH_CHALLENGE_SIZE 32U
#define FACTORY_AUTH_HARDWARE_HASH_SIZE 32U
#define FACTORY_AUTH_SIGNATURE_SIZE 64U

/*
 * FactoryAuthenticate.signature is Ed25519 over this 32-byte SHA-256 digest:
 *   "UKEY_FACTORY_AUTH_V1" ||
 *   protocol_version_be32 || key_id_be32 || init_state_be32 ||
 *   challenge[32] || hardware_hash[32]
 */

void factory_auth_init(void);

bool factory_auth_create_challenge(
    uint8_t challenge[FACTORY_AUTH_CHALLENGE_SIZE],
    uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE],
    uint32_t *init_state);

bool factory_auth_verify(
    uint32_t protocol_version, uint32_t key_id, uint32_t init_state,
    const uint8_t challenge[FACTORY_AUTH_CHALLENGE_SIZE],
    const uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE],
    const uint8_t signature[FACTORY_AUTH_SIGNATURE_SIZE]);

bool factory_auth_is_authenticated(void);
void factory_auth_note_activity(void);
void factory_auth_lock(void);

uint32_t factory_auth_get_init_state(void);
void factory_auth_get_hardware_hash(
    uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE]);

#endif  // _FACTORY_AUTH_H_
