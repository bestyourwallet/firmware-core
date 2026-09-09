#include "factory_auth.h"

#include <string.h>

#include "common.h"
#include "device.h"
#include "ed25519-donna/ed25519.h"
#include "factory_keys.h"
#include "memzero.h"
#include "rand.h"
#include "se_acl16.h"
#include "sha2.h"

#define FACTORY_CHALLENGE_TIMEOUT_MS (30U * 1000U)
#define FACTORY_SESSION_IDLE_TIMEOUT_MS (60U * 1000U)
#define FACTORY_SESSION_MAX_TIMEOUT_MS (5U * 60U * 1000U)

typedef enum {
  FACTORY_AUTH_LOCKED = 0,
  FACTORY_AUTH_CHALLENGE_ISSUED,
  FACTORY_AUTH_AUTHENTICATED,
} factory_auth_state_t;

typedef struct {
  factory_auth_state_t state;
  uint8_t challenge[FACTORY_AUTH_CHALLENGE_SIZE];
  uint32_t challenge_created_at;
  uint32_t authenticated_at;
  uint32_t last_activity_at;
} factory_auth_context_t;

static factory_auth_context_t factory_auth_ctx;

static const uint8_t factory_auth_domain[] = "UKEY_FACTORY_AUTH_V1";

static bool elapsed(uint32_t start, uint32_t timeout) {
  return (uint32_t)(hal_ticks_ms() - start) >= timeout;
}

static void sha256_update_u32_be(SHA256_CTX *ctx, uint32_t value) {
  const uint8_t encoded[4] = {
      (uint8_t)(value >> 24),
      (uint8_t)(value >> 16),
      (uint8_t)(value >> 8),
      (uint8_t)value,
  };
  sha256_Update(ctx, encoded, sizeof(encoded));
}

uint32_t factory_auth_get_init_state(void) {
  uint32_t init_state = 0;
  init_state |= device_serial_set() ? 1U : 0U;
  init_state |= se_has_cerrificate() ? (1U << 2) : 0U;
  return init_state;
}

void factory_auth_get_hardware_hash(
    uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE]) {
  uint8_t uid[12];
  device_get_stm32_unique_id(uid);
  sha256_Raw(uid, sizeof(uid), hardware_hash);
  memzero(uid, sizeof(uid));
}

void factory_auth_lock(void) {
  memzero(&factory_auth_ctx, sizeof(factory_auth_ctx));
  factory_auth_ctx.state = FACTORY_AUTH_LOCKED;
}

void factory_auth_init(void) { factory_auth_lock(); }

bool factory_auth_create_challenge(
    uint8_t challenge[FACTORY_AUTH_CHALLENGE_SIZE],
    uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE],
    uint32_t *init_state) {
  if (challenge == NULL || hardware_hash == NULL || init_state == NULL) {
    return false;
  }

  factory_auth_lock();
  random_buffer(factory_auth_ctx.challenge, sizeof(factory_auth_ctx.challenge));
  factory_auth_ctx.challenge_created_at = hal_ticks_ms();
  factory_auth_ctx.state = FACTORY_AUTH_CHALLENGE_ISSUED;

  memcpy(challenge, factory_auth_ctx.challenge,
         sizeof(factory_auth_ctx.challenge));
  factory_auth_get_hardware_hash(hardware_hash);
  *init_state = factory_auth_get_init_state();
  return true;
}

bool factory_auth_verify(
    uint32_t protocol_version, uint32_t key_id, uint32_t init_state,
    const uint8_t challenge[FACTORY_AUTH_CHALLENGE_SIZE],
    const uint8_t hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE],
    const uint8_t signature[FACTORY_AUTH_SIGNATURE_SIZE]) {
  uint8_t actual_hardware_hash[FACTORY_AUTH_HARDWARE_HASH_SIZE];
  uint8_t digest[SHA256_DIGEST_LENGTH];
  const uint8_t *public_key = NULL;
  bool verified = false;

  if (challenge == NULL || hardware_hash == NULL || signature == NULL ||
      factory_auth_ctx.state != FACTORY_AUTH_CHALLENGE_ISSUED ||
      elapsed(factory_auth_ctx.challenge_created_at,
              FACTORY_CHALLENGE_TIMEOUT_MS)) {
    factory_auth_lock();
    return false;
  }

  factory_auth_get_hardware_hash(actual_hardware_hash);

  if (protocol_version == FACTORY_AUTH_PROTOCOL_VERSION &&
      init_state == factory_auth_get_init_state() &&
      memcmp(challenge, factory_auth_ctx.challenge,
             FACTORY_AUTH_CHALLENGE_SIZE) == 0 &&
      memcmp(hardware_hash, actual_hardware_hash,
             FACTORY_AUTH_HARDWARE_HASH_SIZE) == 0 &&
      factory_auth_get_public_key(key_id, &public_key)) {
    SHA256_CTX ctx = {0};
    sha256_Init(&ctx);
    sha256_Update(&ctx, factory_auth_domain, sizeof(factory_auth_domain) - 1);
    sha256_update_u32_be(&ctx, protocol_version);
    sha256_update_u32_be(&ctx, key_id);
    sha256_update_u32_be(&ctx, init_state);
    sha256_Update(&ctx, challenge, FACTORY_AUTH_CHALLENGE_SIZE);
    sha256_Update(&ctx, hardware_hash, FACTORY_AUTH_HARDWARE_HASH_SIZE);
    sha256_Final(&ctx, digest);

    verified =
        ed25519_sign_open(digest, sizeof(digest), public_key, signature) == 0;
  }

  /* A challenge is single-use even when verification fails. */
  memzero(factory_auth_ctx.challenge, sizeof(factory_auth_ctx.challenge));
  memzero(actual_hardware_hash, sizeof(actual_hardware_hash));
  memzero(digest, sizeof(digest));

  if (!verified) {
    factory_auth_lock();
    return false;
  }

  factory_auth_ctx.authenticated_at = hal_ticks_ms();
  factory_auth_ctx.last_activity_at = factory_auth_ctx.authenticated_at;
  factory_auth_ctx.state = FACTORY_AUTH_AUTHENTICATED;
  return true;
}

bool factory_auth_is_authenticated(void) {
  if (factory_auth_ctx.state != FACTORY_AUTH_AUTHENTICATED) {
    return false;
  }

  if (elapsed(factory_auth_ctx.last_activity_at,
              FACTORY_SESSION_IDLE_TIMEOUT_MS) ||
      elapsed(factory_auth_ctx.authenticated_at,
              FACTORY_SESSION_MAX_TIMEOUT_MS)) {
    factory_auth_lock();
    return false;
  }

  return true;
}

void factory_auth_note_activity(void) {
  if (factory_auth_is_authenticated()) {
    factory_auth_ctx.last_activity_at = hal_ticks_ms();
  }
}
