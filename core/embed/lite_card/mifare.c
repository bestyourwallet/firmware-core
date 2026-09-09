#include "mifare.h"

#include "aes/aes.h"
#include "device.h"
#include "nfc.h"
#include "pn532.h"
#include "rand.h"
#include "se_acl16.h"
#include "sha2.h"
#include "stdbool.h"
#include "string.h"

enum {
  NONE = 0,        // Empty
  SEED_CARD = 10,  // Card
  SEED_RING = 20,  // Ring
};

// clang-format off
#define CMD_GET_VERSION     0x60        // Get version command
#define CMD_READ            0x30        // Read command (4 pages: 16 bytes)
#define CMD_FAST_READ       0x3A        // Fast read command
#define CMD_WRITE           0xA2        // Write command
#define CMD_READ_CNT        0x39        // Read counter command
#define CMD_INCR_CNT        0xA3        // Increment counter command
#define CMD_READ_SIG        0x3C        // Read signature command
#define CMD_WRITE_SIG       0xA9        // Write signature command
#define CMD_LOCK_SIG        0xAC        // Lock signature command
#define CMD_AUTHENTICATE_P1 0x1A        // Authentication command, part 1
#define CMD_AUTHENTICATE_P2 0xAF        // Authentication command, part 2

#define MNEMONIC_START_PAGE 0x10        // First mnemonic storage page
#define PUBLIC_PAGE         0x04        // Public data page (retry count)
#define RETRY_COUNT_POS     0x00        // Retry count position on the public data page
#define NEW_TAG_POS         0x03        // New-card flag position on the public data page (0x00 = new card)
#define INFO_PAGE           0x05        // Information page (model and type)
#define MODEL_POS           0x00        // Model position on the information page
#define TYPE_POS            0x01        // Type position on the information page
#define ID_PAGE             0x06        // Custom data page
#define ID_MAX_SIZE         24U         // Maximum custom data size in bytes

#define USE_DATA_START_PAGE 0x04        // First user data page
#define USE_DATA_END_PAGE   0x27        // Last user data page

#define MIFARE_START_PAGE   0x04        // First card page
#define MIFARE_END_PAGE     0x3B        // Last card page

#define NICKNAME_MAX_LENGTH 12               // Maximum nickname length
#define NICKNAME_END_PAGE USE_DATA_END_PAGE  // Last nickname page
#define NICKNAME_START_PAGE \
  (NICKNAME_END_PAGE - (NICKNAME_MAX_LENGTH + 3) / 4 + 1)  // First nickname page

#define AES_KEY0 0x30  // DataProtKey
#define AES_KEY1 0x34  // UIDRetrKey

#define MAX_RETRY 10  // Maximum authentication attempts

#define SET_REG_BIT(reg, bit, val) \
  ((val) ? ((reg) |= (1U << (bit))) : ((reg) &= ~(1U << (bit))))

static int mifare_fast_read(uint8_t sta_page, uint8_t end_page,
                            uint8_t* response, uint16_t* response_len);

#define CMAC_CONST_RB 0x87
#define CMAC_TAG_SIZE 8

static uint8_t ses_auth_mac_key[16];
static uint16_t cmd_ctr;
static bool cmac_session_active;

/**
 * @brief Generate an AES key from a password.
 * @param password
 * @param aes_key
 * @return
 */
int password_to_aes_key(const char* password, uint8_t* aes_key) {
  SHA256_CTX ctx;
  uint8_t hash[32];

  sha256_Init(&ctx);
  sha256_Update(&ctx, (const uint8_t*)password, strlen(password));
  sha256_Final(&ctx, hash);

  memcpy(aes_key, hash, 16);
  return 0;
}

/**
 * Rotate a byte array left by one byte.
 * @param data
 * @param data_len
 * @return
 */
static void rot_left(uint8_t* data, uint16_t data_len) {
  uint8_t buf = data[0];
  for (int i = 1; i < data_len; i++) {
    data[i - 1] = data[i];
  }
  data[data_len - 1] = buf;
}

static uint16_t mnemonic_crc16(const uint8_t* data, uint16_t len) {
  uint16_t crc = 0xFFFF;

  while (len--) {
    crc ^= *data++;
    for (int i = 0; i < 8; i++) {
      if (crc & 0x0001) {
        crc = (crc >> 1) ^ 0xA001;
      } else {
        crc >>= 1;
      }
    }
  }

  return crc;
}

static int get_mnemonic_length(uint16_t* total_len) {
  uint8_t first_page[4] = {0};
  uint16_t resp_len = 0;

  if (total_len == NULL) {
    return false;
  }

  if (mifare_fast_read(MNEMONIC_START_PAGE, MNEMONIC_START_PAGE, first_page,
                       &resp_len) != true) {
    return -1;
  }

  if (resp_len < 4) {
    return false;
  }

  uint8_t type = first_page[0];
  if (type < 1 || type > 5) {
    return false;
  }

  *total_len = 1 + ((type - 1) * 4 + 16) + 2;  // TYPE + ENT + CRC16
  return true;
}

/**
 * Left-shift a 128-bit block by 1 bit.
 */
static void cmac_block_left_shift(const uint8_t* input, uint8_t* output) {
  uint8_t carry = 0;
  for (int i = 15; i >= 0; i--) {
    output[i] = (input[i] << 1) | carry;
    carry = (input[i] >> 7) & 1;
  }
}

/**
 * XOR two 128-bit blocks.
 */
static void cmac_block_xor(const uint8_t* a, const uint8_t* b, uint8_t* out) {
  for (int i = 0; i < 16; i++) {
    out[i] = a[i] ^ b[i];
  }
}

/**
 * Generate CMAC subkeys K1 and K2 per NIST SP 800-38B.
 */
static void cmac_generate_subkeys(const uint8_t* key, uint8_t* K1,
                                  uint8_t* K2) {
  aes_encrypt_ctx ctx;
  aes_encrypt_key128(key, &ctx);

  uint8_t L[16];
  uint8_t zero_block[16] = {0};
  aes_encrypt(zero_block, L, &ctx);

  cmac_block_left_shift(L, K1);
  if (L[0] & 0x80) {
    K1[15] ^= CMAC_CONST_RB;
  }

  cmac_block_left_shift(K1, K2);
  if (K1[0] & 0x80) {
    K2[15] ^= CMAC_CONST_RB;
  }
}

/**
 * AES-CMAC per NIST SP 800-38B.
 * Produces a 16-byte MAC tag.
 */
static void aes_cmac(const uint8_t* key, const uint8_t* msg, uint16_t msg_len,
                     uint8_t* mac) {
  uint8_t K1[16], K2[16];
  cmac_generate_subkeys(key, K1, K2);

  uint16_t n_blocks = (msg_len + 15) / 16;
  bool complete_last_block;

  if (n_blocks == 0) {
    n_blocks = 1;
    complete_last_block = false;
  } else {
    complete_last_block = (msg_len % 16 == 0);
  }

  uint8_t M_last[16] = {0};
  uint16_t last_offset = (n_blocks - 1) * 16;
  uint8_t last_len = (uint8_t)(msg_len - last_offset);

  if (complete_last_block) {
    cmac_block_xor(msg + last_offset, K1, M_last);
  } else {
    uint8_t padded[16] = {0};
    if (last_len > 0) {
      memcpy(padded, msg + last_offset, last_len);
    }
    padded[last_len] = 0x80;
    cmac_block_xor(padded, K2, M_last);
  }

  aes_encrypt_ctx ctx;
  aes_encrypt_key128(key, &ctx);

  uint8_t X[16] = {0};
  uint8_t Y[16];

  for (uint16_t i = 0; i < n_blocks - 1; i++) {
    cmac_block_xor(X, msg + i * 16, Y);
    aes_encrypt(Y, X, &ctx);
  }

  cmac_block_xor(X, M_last, Y);
  aes_encrypt(Y, mac, &ctx);
}

/**
 * Derive SesAuthMACKey from authentication key and random nonces
 * per NIST SP 800-108 counter mode (Section 8.8.1 of datasheet).
 *
 * SV2 = 5Ah||A5h||00h||01h||00h||80h||
 *        RndA[15..14]||
 *        (RndA[13..8] XOR RndB[15..10])||
 *        RndB[9..0]||
 *        RndA[7..0]
 *
 * SesAuthMACKey = AES-CMAC(Kx, SV2)
 */
static void derive_session_key(const uint8_t* auth_key, const uint8_t* rndA,
                               const uint8_t* rndB) {
  uint8_t sv2[32];

  sv2[0] = 0x5A;
  sv2[1] = 0xA5;
  sv2[2] = 0x00;
  sv2[3] = 0x01;
  sv2[4] = 0x00;
  sv2[5] = 0x80;

  // Follow the datasheet/AN13452 byte order as presented in the auth examples.
  sv2[6] = rndA[0];
  sv2[7] = rndA[1];

  for (int i = 0; i < 6; i++) {
    sv2[8 + i] = rndA[2 + i] ^ rndB[i];
  }
  for (int i = 0; i < 10; i++) {
    sv2[14 + i] = rndB[6 + i];
  }
  for (int i = 0; i < 8; i++) {
    sv2[24 + i] = rndA[8 + i];
  }

  aes_cmac(auth_key, sv2, sizeof(sv2), ses_auth_mac_key);
}

/**
 * NXP convention: truncate 16-byte CMAC to 8 bytes by picking odd-indexed
 * bytes. out[i] = full[2*i + 1]  for i = 0..7
 */
static void cmac_truncate(const uint8_t* full, uint8_t* out) {
  for (int i = 0; i < CMAC_TAG_SIZE; i++) {
    out[i] = full[2 * i + 1];
  }
}

void mifare_clear_session(void) {
  cmac_session_active = false;
  cmd_ctr = 0;
  memset(ses_auth_mac_key, 0, sizeof(ses_auth_mac_key));
}

/**
 * @brief Write Mifare card data
 *
 * 4 bytes
 *
 * @param page
 * @param data
 * @return int
 */
static uint8_t mifare_write(uint8_t page, const uint8_t* data) {
  if (cmac_session_active) {
    uint8_t cmd[6 + CMAC_TAG_SIZE];
    cmd[0] = CMD_WRITE;
    cmd[1] = page;
    memcpy(cmd + 2, data, 4);

    uint8_t cmac_in[8] = {cmd_ctr & 0xFF, (cmd_ctr >> 8) & 0xFF,
                          CMD_WRITE,      page,
                          data[0],        data[1],
                          data[2],        data[3]};
    uint8_t mac_full[16];
    aes_cmac(ses_auth_mac_key, cmac_in, sizeof(cmac_in), mac_full);
    cmac_truncate(mac_full, cmd + 6);

    uint8_t resp[16];
    uint16_t resp_len = sizeof(resp);
    if (pn532_InCommunicateThru(cmd, sizeof(cmd), resp, &resp_len) != true) {
      cmac_session_active = false;
      return false;
    }
    if (resp_len < CMAC_TAG_SIZE) {
      cmac_session_active = false;
      return false;
    }

    cmd_ctr++;
    uint8_t ack_in[2] = {cmd_ctr & 0xFF, (cmd_ctr >> 8) & 0xFF};
    uint8_t expected_full[16], expected[CMAC_TAG_SIZE];
    aes_cmac(ses_auth_mac_key, ack_in, 2, expected_full);
    cmac_truncate(expected_full, expected);
    if (memcmp(expected, resp, CMAC_TAG_SIZE) != 0) {
      cmac_session_active = false;
      return false;
    }

    cmd_ctr++;
  } else {
    uint8_t cmd[6] = {CMD_WRITE, page, data[0], data[1], data[2], data[3]};
    if (!pn532_inDataExchange(cmd, sizeof(cmd), NULL, 0)) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Read Mifare card data
 *
 * 4 pages = 16 bytes, CMAC mode additionally returns an 8-byte checksum
 *
 * @param page
 * @param response_data
 * @param response_len
 * @return int
 */
static int __attribute__((unused))
mifare_read(uint8_t page, uint8_t* response_data, uint16_t* response_len) {
  if (cmac_session_active) {
    uint8_t cmd[2 + CMAC_TAG_SIZE];
    cmd[0] = CMD_READ;
    cmd[1] = page;

    uint8_t cmac_in[4] = {cmd_ctr & 0xFF, (cmd_ctr >> 8) & 0xFF, CMD_READ,
                          page};
    uint8_t mac_full[16];
    aes_cmac(ses_auth_mac_key, cmac_in, sizeof(cmac_in), mac_full);
    cmac_truncate(mac_full, cmd + 2);

    uint8_t full_resp[26];
    uint16_t full_resp_len = sizeof(full_resp) - 2;
    if (pn532_InCommunicateThru(cmd, sizeof(cmd), full_resp + 2,
                                &full_resp_len) != true) {
      cmac_session_active = false;
      return false;
    }
    if (full_resp_len < CMAC_TAG_SIZE) {
      cmac_session_active = false;
      return false;
    }

    cmd_ctr++;
    uint16_t data_len = full_resp_len - CMAC_TAG_SIZE;
    full_resp[0] = cmd_ctr & 0xFF;
    full_resp[1] = (cmd_ctr >> 8) & 0xFF;

    uint8_t expected_full[16], expected[CMAC_TAG_SIZE];
    aes_cmac(ses_auth_mac_key, full_resp, 2 + data_len, expected_full);
    cmac_truncate(expected_full, expected);
    if (memcmp(expected, full_resp + 2 + data_len, CMAC_TAG_SIZE) != 0) {
      cmac_session_active = false;
      return false;
    }

    memcpy(response_data, full_resp + 2, data_len);
    *response_len = data_len;
    cmd_ctr++;
  } else {
    uint8_t cmd[2] = {CMD_READ, page};
    if (!pn532_inDataExchange(cmd, sizeof(cmd), response_data, response_len)) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Quickly read Mifare card data
 *
 * Multi-page, CMAC mode automatically appends/verifies 8-byte MAC
 *
 * @param sta_page
 * @param end_page
 * @param response
 * @param response_len
 * @return int
 */
static int mifare_fast_read(uint8_t sta_page, uint8_t end_page,
                            uint8_t* response, uint16_t* response_len) {
  if (end_page < sta_page || sta_page < MIFARE_START_PAGE ||
      end_page > MIFARE_END_PAGE) {
    return false;
  }
  if (cmac_session_active) {
    uint8_t cmd[3 + CMAC_TAG_SIZE];
    cmd[0] = CMD_FAST_READ;
    cmd[1] = sta_page;
    cmd[2] = end_page;

    uint8_t cmac_in[5] = {cmd_ctr & 0xFF, (cmd_ctr >> 8) & 0xFF, CMD_FAST_READ,
                          sta_page, end_page};
    uint8_t mac_full[16];
    aes_cmac(ses_auth_mac_key, cmac_in, sizeof(cmac_in), mac_full);
    cmac_truncate(mac_full, cmd + 3);

    uint8_t full_resp[258];
    uint16_t full_resp_len = sizeof(full_resp) - 2;
    if (pn532_InCommunicateThru(cmd, sizeof(cmd), full_resp + 2,
                                &full_resp_len) != true) {
      cmac_session_active = false;
      return false;
    }
    if (full_resp_len < CMAC_TAG_SIZE) {
      cmac_session_active = false;
      return false;
    }

    cmd_ctr++;
    uint16_t data_len = full_resp_len - CMAC_TAG_SIZE;
    full_resp[0] = cmd_ctr & 0xFF;
    full_resp[1] = (cmd_ctr >> 8) & 0xFF;

    uint8_t expected_full[16], expected[CMAC_TAG_SIZE];
    aes_cmac(ses_auth_mac_key, full_resp, 2 + data_len, expected_full);
    cmac_truncate(expected_full, expected);
    if (memcmp(expected, full_resp + 2 + data_len, CMAC_TAG_SIZE) != 0) {
      cmac_session_active = false;
      return false;
    }

    memcpy(response, full_resp + 2, data_len);
    *response_len = data_len;
    cmd_ctr++;
  } else {
    uint8_t cmd[3] = {CMD_FAST_READ, sta_page, end_page};
    if (pn532_InCommunicateThru(cmd, sizeof(cmd), response, response_len) !=
        true) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Get the version object
 *
 * @param version
 * @return int
 */
int get_version(uint8_t* version) {
  uint8_t response[8];
  uint16_t response_length = sizeof(response);

  uint8_t cmd[1] = {CMD_GET_VERSION};
  if (pn532_InCommunicateThru(cmd, sizeof(cmd), response, &response_length) !=
      true) {
    return false;
  }
  return true;
}

/**
 * AES setting protection settings
 * @param mode 0: Write access is restricted, but read access is allowed. 1: Both write and read access are restricted.
 * @return
 */
int protection_settings(uint8_t mode) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  if (mode == 0) {
    response_data[0] &= ~(1u << 7);
  } else if (mode == 1) {
    response_data[3] |= (1u << 7);
  } else {
    return false;
  }
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set read-only page
 * @param start_page Home page
 * @param end_page   End page
 * @return
 */
int read_only_page_settings(uint8_t start_page, uint8_t end_page) {
  if (start_page > end_page || start_page < 0x04 || end_page > 0x0F) {
    return false;
  }
  uint8_t page_data[4] = {0};
  uint16_t lock = 0;
  for (int i = start_page; i <= end_page; i++) {
    lock |= 0x01 << i;
  }
  page_data[2] = lock & 0xFF;
  page_data[3] = (lock >> 8) & 0xFF;
  if (mifare_write(0x02, page_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set the maximum number of AES attempts
 * @param max_attempts
 * @return
 */
int set_aes_attempts(uint16_t max_attempts) {
  if (max_attempts > 1022) {
    return false;
  }
  uint8_t response_data[16] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != 0) {
    return false;
  }
  response_data[2] = max_attempts & 0xFF;
  response_data[3] = max_attempts >> 8 & 0x03;
  if (mifare_write(0x2A, response_data) != 0) {
    return false;
  }
  return true;
}

/**
 * Set a random ID
 * @param enable
 * @return
 */
int set_random_id(uint8_t enable) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x29, 0x29, response_data, &response_len) != true) {
    return false;
  }
  response_data[0] =
      enable ? (response_data[0] | 0x01) : (response_data[0] & ~0x01);
  if (mifare_write(0x29, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set AES protected page
 * @param start_page
 * @param enable
 * @return
 */
int set_aes_protection(uint8_t start_page, bool enable) {
  uint8_t AUTH0 = 0xFF;
  if (start_page > 0x3B) {
    return false;
  }
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x29, 0x29, response_data, &response_len) != true) {
    return false;
  }
  AUTH0 = enable ? start_page : 0xFF;
  response_data[3] = (response_data[3] & 0x80) | AUTH0;
  if (mifare_write(0x29, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Data access restrictions when configuration is without verification
 * @param restrict_read_and_write 0: Write-only restriction; 1: Read and write restrictions
 * @return
 */
int set_memory_protection(uint8_t restrict_read_and_write) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 7, restrict_read_and_write);
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set counter increment unauthorized access permission
 * @param enable
 * @return
 */
int set_counter_inc_unauth_allowed(uint8_t enable) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 3, enable & 0x01);
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set counter read unauthorized access permission
 * @param enable
 * @return
 */
int set_counter_read_unauth_allowed(uint8_t enable) {
  if (enable > 1) {
    return false;
  }
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 2, enable & 0x01);
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Virtual Card Architecture
 * @param vctid_value
 * @return
 */
int set_vctid(uint8_t vctid_value) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  response_data[1] = vctid_value;
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Set the number of access restrictions for failed authentication attempts
 * @param limit
 * @return
 */
int set_auth_limit(uint16_t limit, uint8_t enable) {
  if (limit > 1022) {
    return false;
  }
  if (!enable) {
    limit = 0;
  }
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  response_data[2] = limit & 0xFF;
  response_data[3] = limit >> 8 & 0x03;
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Activate Secure Messaging
 * @param enable
 * @return
 */
int set_secure_messaging(uint8_t enable) {
  if (enable > 1) {
    return false;
  }
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x29, 0x29, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 1, enable & 0x01);
  if (mifare_write(0x29, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Permanently lock AES_KEY0
 * @return
 */
int lock_aes_key0(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2D, 0x2D, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 6, 0x01);
  if (mifare_write(0x2D, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Permanently lock AES_KEY1
 * @return
 */
int lock_aes_key1(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2D, 0x2D, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 7, 0x01);
  if (mifare_write(0x2D, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Permanently lock LOCK_AES_KEY0 and LOCK_AES_KEY1 configuration bits
 * @return
 */
int lock_key_configuration(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2D, 0x2D, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 5, 0x01);
  if (mifare_write(0x2D, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * Permanently lock user configuration elements
 * @return
 */
int lock_user_configuration(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(0x2A, 0x2A, response_data, &response_len) != true) {
    return false;
  }
  SET_REG_BIT(response_data[0], 6, 0x01);
  if (mifare_write(0x2A, response_data) != true) {
    return false;
  }
  return true;
}

/**
 * @brief Set the aes key object
 *
 * Set the AES key
 *
 * KEY = [ K1 , K2 , K3 , K4
 *         K5 , K6 , K7 , K8
 *         K9 , K10, K11, K12
 *         K13, K14, K15, K16 ]
 *
 * Page0 = [ K16, K15, K14, K13 ]
 * Page1 = [ K12, K11, K10, K9  ]
 * Page2 = [ K8 , K7 , K6 , K5  ]
 * Page3 = [ K4 , K3 , K2 , K1  ]
 *
 * mode 0: DataProtKey
 * mode 1: UIDRetrKey
 *
 * @param key
 * @param mode
 * @return int
 */
int set_aes_key(const uint8_t* key, uint8_t mode) {
  const uint8_t page = mode ? AES_KEY1 : AES_KEY0;
  for (int i = 0; i < 4; i++) {
    const uint8_t* key_data = key + (3 - i) * 4;
    const uint8_t data_page[] = {key_data[3], key_data[2], key_data[1],
                                 key_data[0]};
    if (mifare_write(page + i, data_page) != true) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Mifare card authentication
 *
 * PCD -> PICC
 *
 *
 * @param key
 * @param key_no
 * @return int
 */
int aes_authenticate(const uint8_t* key, uint8_t key_no) {
  cmac_session_active = false;
  cmd_ctr = 0;
  memset(ses_auth_mac_key, 0, sizeof(ses_auth_mac_key));

  uint8_t response[128];
  uint16_t response_length = sizeof(response);

  aes_encrypt_ctx enc;
  aes_decrypt_ctx dec;
  aes_encrypt_key128(key, &enc);
  aes_decrypt_key128(key, &dec);

  /*  Part 1  */
  uint8_t cmd_p1[2] = {CMD_AUTHENTICATE_P1, key_no};
  bool res = pn532_InCommunicateThru(cmd_p1, sizeof(cmd_p1), response,
                                     &response_length);
  if (res != true) {
    return false;
  }
  if (response_length != 17 || response[0] != CMD_AUTHENTICATE_P2) {
    return false;
  }
  uint8_t ciphertext_part1[16] = {0};  // Part 1 ciphertext
  uint8_t rndB[16] = {0};              // Decrypted random number B
  uint8_t iv_dec[16] = {0};            // Decryption initialization vector
  memcpy(ciphertext_part1, response + 1,
         sizeof(ciphertext_part1));  // Copy the Part 1 ciphertext
  if (aes_cbc_decrypt(response + 1, rndB, sizeof(rndB), iv_dec, &dec) !=
      EXIT_SUCCESS) {
    return false;
  }

  /*  Part 2  */
  uint8_t rndA[16] = {0};   // Random number A
  random_buffer(rndA, 16);  // Generate random number A

  uint8_t rndB_rot[16];                  // Rotated random number B
  memcpy(rndB_rot, rndB, sizeof(rndB));  // Copy random number B
  rot_left(rndB_rot, sizeof(rndB_rot));  // Rotate random number B

  uint8_t plaintext[32] = {0};            // Plaintext
  uint8_t plaintext_enc[32] = {0};        // Encrypted plaintext
  memcpy(plaintext, rndA, sizeof(rndA));  // Copy random number A
  memcpy(plaintext + sizeof(rndA), rndB_rot,
         sizeof(rndB_rot));  // Copy the rotated random number B

  uint8_t iv_enc[16] = {0};  // Part 2 encryption initialization vector
  if (aes_cbc_encrypt(plaintext, plaintext_enc, sizeof(plaintext_enc), iv_enc,
                      &enc) != EXIT_SUCCESS) {
    return false;
  }

  uint8_t cmd_p2[33];                      // Part 2 command
  cmd_p2[0] = CMD_AUTHENTICATE_P2;         // Part 2 command header
  memcpy(cmd_p2 + 1, plaintext_enc,
         sizeof(plaintext_enc));  // Copy the encrypted plaintext
  response_length = sizeof(response);
  res = pn532_InCommunicateThru(cmd_p2, sizeof(cmd_p2), response,
                                &response_length);
  if (res != true) {
    return false;
  }
  if (response_length < 17 || response[0] != 0x00) {
    return false;
  }

  /*  Part 3  */
  uint8_t rndA_prime[16];             // Decrypted random number A
  memset(iv_dec, 0, sizeof(iv_dec));  // Reset the decryption IV
  if (aes_cbc_decrypt(response + 1, rndA_prime, sizeof(rndA_prime), iv_dec,
                      &dec) != EXIT_SUCCESS) {
    return false;
  }

  uint8_t rndA_rot[16];                  // Rotated random number A
  memcpy(rndA_rot, rndA, 16);            // Copy random number A
  rot_left(rndA_rot, sizeof(rndA_rot));  // Rotate random number A

  if (memcmp(rndA_rot, rndA_prime, sizeof(rndA_prime)) != 0) {
    return false;
  }

  derive_session_key(key, rndA, rndB);
  cmd_ctr = 0;
  cmac_session_active = true;

  return true;
}

/**
 * @brief Read Mifare card signature
 *
 * @param signature
 * @return int
 */
int read_signature(uint8_t* signature) {
  (void)signature;
  return false;
}

/**
 * @brief Write Mifare card signature
 *
 * @param signature
 * @return int
 */
int write_signature(const uint8_t* signature) {
  (void)signature;
  return false;
}

/**
 * @brief Lock Mifare card signature
 *
 * @return int
 */
int lock_signature(void) { return false; }

/**
 * @brief Read card nickname
 *
 * @param nick_name
 * @return
 */
uint8_t read_nick_name(char* nick_name) {
  uint8_t nick_name_buffer[(NICKNAME_END_PAGE - NICKNAME_START_PAGE + 1) * 4] =
      {0};
  uint16_t read_len = 0;
  if (mifare_fast_read(NICKNAME_START_PAGE, NICKNAME_END_PAGE, nick_name_buffer,
                       &read_len) != true) {
    printf("read_nick_name mifare_fast_read failed\n");
    return false;
  }
  memcpy(nick_name, nick_name_buffer, read_len);
  return true;
}

/**
 * @brief Write card nickname
 *
 * @param str
 * @return
 */
uint8_t write_nick_name(const char* str) {
  uint8_t nick_name_len = (uint8_t)strlen(str);
  if (nick_name_len > NICKNAME_MAX_LENGTH) {
    printf("write_nick_name failed: nickname too long\n");
    return false;
  }
  uint8_t nick_name_buffer[(NICKNAME_END_PAGE - NICKNAME_START_PAGE + 1) * 4] =
      {0};
  memcpy(nick_name_buffer, str, nick_name_len);
  for (int i = 0; i <= (NICKNAME_END_PAGE - NICKNAME_START_PAGE); i++) {
    uint8_t page_data[4] = {0};
    memcpy(page_data, nick_name_buffer + i * 4, 4);
    if (mifare_write(NICKNAME_START_PAGE + i, page_data) != true) {
      printf("write_nick_name mifare_write page %d failed\n",
             NICKNAME_START_PAGE + i);
      return false;
    }
  }
  return true;
}

/**
 * @brief Read mnemonic
 *
 * @param buffer
 * @param buffer_len
 * @return uint8_t
 */
int read_mnemonic(uint8_t* buffer, uint16_t* out_len) {
  if (buffer == NULL || out_len == NULL) {
    return false;
  }
  uint16_t total_len = 0;
  int length_status = get_mnemonic_length(&total_len);
  if (length_status != true) {
    if (length_status < 0) {
      printf("read_mnemonic first fail\n");
    }
    return false;
  }

  uint8_t pages = (total_len + 3) / 4;
  uint8_t end_page = MNEMONIC_START_PAGE + pages - 1;

  uint8_t temp[48] = {0};
  uint16_t temp_len = 0;

  if (mifare_fast_read(MNEMONIC_START_PAGE, end_page, temp, &temp_len) !=
      true) {
    return false;
  }

  if (temp_len < total_len) {
    return false;
  }

  uint16_t expected_crc = mnemonic_crc16(temp, total_len - 2);
  uint16_t actual_crc = temp[total_len - 2] | (temp[total_len - 1] << 8);
  if (expected_crc != actual_crc) {
    return false;
  }

  memcpy(buffer, temp, total_len);
  *out_len = total_len;

  return true;
}

int has_mnemonic(uint8_t* has_data) {
  if (has_data == NULL) {
    return false;
  }

  uint16_t total_len = 0;
  int length_status = get_mnemonic_length(&total_len);
  if (length_status < 0) {
    return false;
  }
  if (length_status == false) {
    *has_data = false;
    return true;
  }

  uint8_t temp[48] = {0};
  uint16_t temp_len = 0;
  uint8_t pages = (total_len + 3) / 4;
  uint8_t end_page = MNEMONIC_START_PAGE + pages - 1;

  if (mifare_fast_read(MNEMONIC_START_PAGE, end_page, temp, &temp_len) !=
      true) {
    return false;
  }
  if (temp_len < total_len) {
    return false;
  }

  uint16_t expected_crc = mnemonic_crc16(temp, total_len - 2);
  uint16_t actual_crc = temp[total_len - 2] | (temp[total_len - 1] << 8);
  *has_data = expected_crc == actual_crc;
  return true;
}

/**
 * @brief Write mnemonic
 *
 * @param buffer
 * @param buffer_len
 * @return uint8_t
 */
int write_mnemonic(const uint8_t* buffer, uint8_t buffer_len) {
  if (buffer == NULL || buffer_len == 0 || buffer_len > 128) {
    return false;
  }

  uint8_t pages = (buffer_len + 3) / 4;

  for (uint8_t i = 0; i < pages; i++) {
    uint8_t page_data[4] = {0};

    uint8_t offset = i * 4;
    uint8_t copy_len = buffer_len - offset;
    if (copy_len > 4) {
      copy_len = 4;
    }

    memcpy(page_data, buffer + offset, copy_len);
    if (mifare_write(MNEMONIC_START_PAGE + i, page_data) != true) {
      printf("write_mnemonic mifare_write page %u failed\n",
             MNEMONIC_START_PAGE + i);
      return false;
    }
  }

  return true;
}

uint8_t set_remaining_retry(uint8_t retry) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  response_data[RETRY_COUNT_POS] = retry;
  if (mifare_write(PUBLIC_PAGE, response_data) != true) {
    return false;
  }
  return true;
}

uint8_t get_remaining_retry(uint8_t* retry) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  *retry = response_data[RETRY_COUNT_POS];
  return true;
}

uint8_t remaining_retry_decrement(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  if (response_data[RETRY_COUNT_POS] == 0) {
    return true;
  }
  response_data[RETRY_COUNT_POS]--;
  if (mifare_write(PUBLIC_PAGE, response_data) != true) {
    return false;
  }
  return true;
}

uint8_t reset_remaining_retry(void) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  response_data[RETRY_COUNT_POS] = MAX_RETRY;
  if (mifare_write(PUBLIC_PAGE, response_data) != true) {
    return false;
  }
  return true;
}

uint8_t is_card_initialized(uint8_t* initialized) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  *initialized = (response_data[RETRY_COUNT_POS] != MAX_RETRY);
  return true;
}
uint8_t set_new_tag(uint8_t tag) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  response_data[NEW_TAG_POS] = tag;
  if (mifare_write(PUBLIC_PAGE, response_data) != true) {
    return false;
  }
  return true;
}

uint8_t is_card_new(uint8_t* is_new) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(PUBLIC_PAGE, PUBLIC_PAGE, response_data, &response_len) != true) {
    return false;
  }
  *is_new = (response_data[NEW_TAG_POS] == 0x00);
  return true;
}

int get_model(int* model) {
  uint8_t response_data[4] = {0};
  uint16_t response_len = 0;
  if (mifare_fast_read(INFO_PAGE, INFO_PAGE, response_data, &response_len) != true) {
    return false;
  }
  switch (response_data[MODEL_POS]) {
    case SEED_CARD:
      *model = SEED_CARD;
      break;
    case SEED_RING:
      *model = SEED_RING;
      break;
    default:
      *model = NONE;
      break;
  }
  return true;
}

// /**
//  * @brief Read data from a Mifare card page
//  *
//  * @param page
//  * @param response_data
//  * @param response_len
//  * @return uint8_t
//  */
// uint8_t mifare_read_test(uint8_t page, uint8_t* response_data,
//                          uint8_t* response_len) {
//   uint8_t cmd[2] = {CMD_READ, page};
//
//   uint8_t buffer[256] = {0};
//   uint16_t recv_len = sizeof(buffer);
//
//   if (!pn532_inDataExchange(cmd, sizeof(cmd), buffer, &recv_len)) {
//     printf("mifare_read_test failed at page %d\n", page);
//     return false;
//   }
//   memcpy(response_data, buffer, recv_len);
//   *response_len = recv_len;
//   return true;
// }
