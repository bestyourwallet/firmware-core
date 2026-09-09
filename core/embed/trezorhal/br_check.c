/*
 * This file is part of the Trezor project, https://trezor.io/
 *
 * Copyright (C) 2018 Pavol Rusnak <stick@satoshilabs.com>
 *
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdint.h>
#include <string.h>

#include "blake2s.h"
#include "br_check.h"
#include "emmc_fs.h"
#include "flash.h"
#include "hardware_version.h"
#include "sdram.h"
#include "sha2.h"

static char boardloader_version[32] = {0};
#define FW_CHUNK_SIZE 65536

typedef struct {
  char version[16];
  char build_id[16];
} board_info_t;

// clang-format off
#if PRODUCTION

static int ukey_known_boardloader(const uint8_t *hash) {
  if (0 ==
      memcmp(hash,
             "\x41\xe8\xaf\xa7\x3e\x39\xe3\xf7\xdc\x4d\x4f\x00\x5a\x06\x43\xde"
             "\xac\x02\xf4\xf5\x76\x60\x7d\x69\xf4\x37\xc2\x27\x77\x07\x27\x61",
             32)) {
      memcpy(boardloader_version, "1.1.0", strlen("1.1.0"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
             "\x7c\x74\x7c\xe6\x55\xc0\xd5\x01\x5f\xaa\xb9\x46\xfd\x01\xed\xfa"
             "\xf7\xda\x30\x4c\x37\x87\xbf\x81\x46\xf5\x30\x7b\x63\x62\x6a\x2c",
             32)) {
      memcpy(boardloader_version, "1.1.1", strlen("1.1.1"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
            "\xcf\xd7\x9d\xd0\x82\xd8\xf4\xa3\xf7\x5e\x62\xd1\x76\x02\xcf\x44"
            "\xc5\xee\x44\x33\xbd\x6b\x9b\x3f\xd4\x00\x9b\xb3\x2d\x4c\x90\x82",
             32)) {
      memcpy(boardloader_version, "1.1.2", strlen("1.1.2"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
            "\x4a\xcb\xd4\xe0\x95\xea\x0b\x65\x75\x63\x09\xe1\x3e\xeb\x67\x7a"
            "\x88\xdf\xd0\x82\xeb\x27\x9d\xed\x57\xc0\x65\x2c\x8f\x45\x31\x0f",
             32)) {
      memcpy(boardloader_version, "1.2.0", strlen("1.2.0"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
            "\x20\x94\x54\x43\x62\xbe\x9b\x6b\x83\x0e\x37\xbf\x7a\x8d\x7e\xa4"
            "\x72\xf1\x33\x69\x12\x36\x4a\xfd\x9d\x12\x64\xff\x71\xac\xc1\x93",
             32)) {
      memcpy(boardloader_version, "1.2.1", strlen("1.2.1"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
            "\x52\xc2\x0a\x70\xa2\x7d\x32\x66\xc8\x1f\x0f\xaa\xb7\x12\x03\x88"
            "\x49\xd0\x06\xcb\x5c\xd9\x09\x28\xf5\x92\x58\x4d\x76\xb7\x56\x01",
             32)) {
      memcpy(boardloader_version, "1.2.2", strlen("1.2.2"));
      return 1;
  }
  return 0;
}

#else

static int ukey_known_boardloader(const uint8_t *hash) {
  if (0 ==
      memcmp(hash,
             "\xc8\xf7\xf8\xf8\xa9\x1b\x52\xf3\xd4\x27\x85\x69\x1c\x9d\x4a\x7b"
             "\xa8\x42\xd3\x50\x95\x38\xb7\x66\xbe\x02\x05\xd5\x13\x49\xf8\xe5",
             32)) {
      memcpy(boardloader_version, "1.1.0", strlen("1.1.0"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
             "\xdf\x03\xf1\x30\x80\xa9\xd2\x0e\xc0\xf0\x87\x66\x0b\x72\xdb\x25"
             "\x27\x68\x1d\xd8\x0d\x82\xa4\x60\x45\x7d\xe5\x58\x01\x16\x71\x1a",
             32)) {
      memcpy(boardloader_version, "1.1.1", strlen("1.1.1"));
      return 1;
  }
  if (0 ==
      memcmp(hash,
            "\x05\x2e\x51\xc6\x5c\xc3\xcf\x18\xf4\xc6\x6d\xa6\x37\x72\xde\x0d"
            "\xf9\xb8\x8f\xc6\x31\x80\x96\x21\xe8\x10\xc5\x02\xa7\xa6\xc6\xa2",
             32)) {
      memcpy(boardloader_version, "1.1.2", strlen("1.1.2"));
      return 1;
  }
  return 0;
}

#endif
// clang-format on

char *get_boardloader_version(void) {
  uint8_t hash[32] = {0};
  SHA256_CTX context = {0};
  uint8_t version_len = 0;

  if (strlen(boardloader_version) == 0) {
    sha256_Init(&context);
    sha256_Update(&context, (uint8_t *)BOARDLOADER_START,
                  BOARDLOADER_SIZE - 32);
    sha256_Update(
        &context,
        (uint8_t*)"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        32);
    sha256_Final(&context, hash);
    sha256_Raw(hash, 32, hash);

    if (!ukey_known_boardloader(hash)) {
      board_info_t *board_info =
          (board_info_t *)(BOARDLOADER_START + BOARDLOADER_SIZE -
                           sizeof(board_info_t));
      version_len = strnlen(board_info->version, sizeof(board_info->version));
      if (version_len > 0 && board_info->version[0] != 0xFF) {
        memcpy(boardloader_version, board_info->version, version_len);
        memcpy(boardloader_version + version_len, "-unk", sizeof("-unk"));
      } else {
        memcpy(boardloader_version, "unknown", strlen("unknown"));
      }
    }
  }

  return boardloader_version;
}

char *get_boardloader_build_id(void) {
  static char boardloader_build_id[16] = {0};
  uint8_t build_id_len = 0;

  board_info_t *board_info =
      (board_info_t *)(BOARDLOADER_START + BOARDLOADER_SIZE -
                       sizeof(board_info_t));
  build_id_len =
      strnlen(board_info->build_id, sizeof(board_info->build_id) - 1);
  if (build_id_len > 0 && board_info->build_id[0] != 0xFF) {
    memcpy(boardloader_build_id, board_info->build_id, build_id_len);
  } else {
    memcpy(boardloader_build_id, "unknown", strlen("unknown"));
  }

  return boardloader_build_id;
}

uint8_t *get_boardloader_hash(void) {
  static uint8_t boardloader_hash[32] = {0};

  sha256_Raw((uint8_t *)BOARDLOADER_START, BOOTLOADER_START - BOARDLOADER_START,
             boardloader_hash);
  sha256_Raw(boardloader_hash, 32, boardloader_hash);

  return boardloader_hash;
}

uint8_t *get_bootloader_hash(void) {
  static uint8_t bootloader_hash[32] = {0};

  uint8_t *p_code_len = (uint8_t *)(BOOTLOADER_START + 12);
  int len = p_code_len[0] + p_code_len[1] * 256 + p_code_len[2] * 256 * 256;
  sha256_Raw((uint8_t *)(BOOTLOADER_START + 1024), len, bootloader_hash);
  sha256_Raw(bootloader_hash, 32, bootloader_hash);

  return bootloader_hash;
}

char *get_bootloader_build_id(void) {
#define BOOTLOADER_BUILD_ID_OFFSET 943
  static char bootloader_build[16] = {0};
  uint8_t build_id_len = 0;

  char *p_build_id = (char *)(BOOTLOADER_START + BOOTLOADER_BUILD_ID_OFFSET);
  build_id_len = strnlen(p_build_id, sizeof(bootloader_build) - 1);
  if (build_id_len > 0) {
    memcpy(bootloader_build, p_build_id, build_id_len);
  } else {
    memcpy(bootloader_build, "unknown", strlen("unknown"));
  }

  return bootloader_build;
}

uint8_t *get_firmware_hash(void) {
  static uint8_t ukey_firmware_hash[32] = {0};
  static bool ukey_firmware_hash_cached = false;
  if (!ukey_firmware_hash_cached) {
    SHA256_CTX context = {0};
    sha256_Init(&context);

    vendor_header *vhdr = (vendor_header *)FIRMWARE_START;
    image_header *hdr = (image_header *)(FIRMWARE_START + vhdr->hdrlen);
    uint32_t innner_firmware_len = 0, outer_firmware_len = 0;

    if (vhdr->magic != 0x56544B55 || hdr->magic != FIRMWARE_IMAGE_MAGIC)
      return ukey_firmware_hash;

    innner_firmware_len =
        hdr->codelen >
                FLASH_FIRMWARE_SECTOR_SIZE * FIRMWARE_INNER_SECTORS_COUNT -
                    vhdr->hdrlen - IMAGE_HEADER_SIZE
            ? FLASH_FIRMWARE_SECTOR_SIZE * FIRMWARE_INNER_SECTORS_COUNT -
                  vhdr->hdrlen - IMAGE_HEADER_SIZE
            : hdr->codelen;
    outer_firmware_len = hdr->codelen - innner_firmware_len;
    sha256_Update(&context,
                  (uint8_t *)FIRMWARE_START + vhdr->hdrlen + IMAGE_HEADER_SIZE,
                  innner_firmware_len);

    if (outer_firmware_len > 0) {
      if (outer_firmware_len > FMC_SDRAM_FIRMWARE_P2_LEN) {
        return ukey_firmware_hash;
      }
      EMMC_PATH_INFO path_info = {0};
      if (!emmc_fs_path_info("0:data/fw_p2.bin", &path_info)) {
        return ukey_firmware_hash;
      }
      if (path_info.path_exist) {
        if (path_info.size != outer_firmware_len) {
          return ukey_firmware_hash;
        }
#if BOOT_ONLY
        uint32_t processed_len = 0;
        if (!emmc_fs_file_read("0:data/fw_p2.bin", 0,
                               (uint32_t *)FMC_SDRAM_FIRMWARE_P2_ADDRESS,
                               outer_firmware_len, &processed_len)) {
          return ukey_firmware_hash;
        }
#endif
        sha256_Update(&context, (uint8_t *)FMC_SDRAM_FIRMWARE_P2_ADDRESS,
                      outer_firmware_len);
      } else if (get_hw_ver() < HW_VER_3P0A) {
        sha256_Update(
            &context,
            flash_get_address(FLASH_SECTOR_FIRMWARE_EXTRA_START, 0, 0),
            outer_firmware_len);
      } else {
        return ukey_firmware_hash;
      }
    }

    sha256_Final(&context, ukey_firmware_hash);

    ukey_firmware_hash_cached = true;
  }

  return ukey_firmware_hash;
}
