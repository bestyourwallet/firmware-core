
#include <string.h>

#include "cmac.h"
#include "ecdsa.h"
#include "nist256p1.h"
#include "rand.h"
#include "scp11.h"
#include "sha2.h"

#include "se_acl16.h"

const static uint8_t sd_cert_verify_pubkey[65] = {
    "\x04\xBB\x10\x4E\xC5\x6F\x1F\x91\x28\xAC\x0E\xAB\xD7\xF0\x85\x33\x8B\xAE"
    "\xDD\xB9\x2D\x2A\x58\x93\x81\x04\xF3\xAA\xC6\x8E\xF0\xD6\x2F\xED\xA9\xB8"
    "\xC6\x57\x70\x86\x20\xBE\x90\xE0\xC2\x83\xD9\x26\x4F\xFB\xBE\x23\xAC\x8B"
    "\x49\x2B\x10\x55\x3D\x56\xF9\xEA\x83\x87\x2C"};

const static uint8_t device_certificate[] = {
    "\x7F\x21\x81\xDB\x93\x10\x43\x45\x52\x54\x5F\x4F\x43\x45\x5F\x45\x43\x4B"
    "\x41\x30\x30\x31\x42\x0D\x75\x6B\x65\x79\x63\x6F\x72\x65\x32\x36\x64\x65"
    "\x76\x5F\x20\x0D\x75\x6B\x65\x79\x63\x6F\x72\x65\x32\x36\x64\x65\x76\x95"
    "\x02\x00\x80\x5F\x25\x04\x20\x26\x09\x04\x5F\x24\x04\x20\x36\x09\x03\x53"
    "\x00\xBF\x20\x00\x7F\x49\x46\xB0\x41\x04\x9D\x6F\x41\xD3\xF8\x7C\xBF\xE0"
    "\xA7\x55\xA2\x83\xAD\xD1\xF9\xC2\x22\xD6\xF3\xDC\xB7\x49\x63\x9A\xCA\xCC"
    "\xDA\x57\x6F\xB8\x81\x25\xFA\x89\xCA\x23\xB3\xDB\x99\x67\xF0\x10\x18\x1D"
    "\x8E\xE6\x99\xA7\x13\x57\x3A\x5E\x23\x07\x93\xC7\xF5\xB2\x71\xC9\xE3\x09"
    "\x62\x7F\xF0\x01\x00\x5F\x37\x47\x30\x45\x02\x21\x00\xF3\x1A\xAF\x7F\x6F"
    "\xC9\x94\xB0\x52\x2A\x60\x8F\x2F\x1D\x67\x00\x36\x34\x11\x20\xBF\xB5\xB7"
    "\x79\x3A\x87\xD7\x64\x2F\x5A\xCB\xAD\x02\x20\x48\x18\xC3\x67\x88\x83\xC5"
    "\xD1\x8E\xDA\xA7\x5A\xBA\xAF\x8D\x07\x59\xCA\x37\x30\xD9\x9C\xA0\xCA\xB9"
    "\x98\xE3\x59\x18\xC6\xE4\xDB"};

// const scp11_shared_info_data scp11_shared_info_data_default = {
//     .scp_id_param = {0x11, 0x07},
//     .key_usage = 0x3c,
//     .key_type = 0x88,
//     .key_length = 0x10,
//     //"pro-lite"
//     .host_id = {0x70,0x72,0x6F,0x2D,0x6C,0x69,0x74,0x65}
//     };

const uint8_t shared_info_buffer[] = {GPC_TLV_SHAREDINFO_SCP_ID_PARAM,
                                      0x02,
                                      0x11,
                                      0x07,
                                      GPC_TLV_SHAREDINFO_KEYUSAGE,
                                      0x01,
                                      0x3c,
                                      GPC_TLV_SHAREDINFO_KEYTYPE,
                                      0x01,
                                      0x88,
                                      GPC_TLV_SHAREDINFO_KEYLENGTH,
                                      0x01,
                                      0x10,
                                      GPC_TLV_SHAREDINFO_HOSTID,
                                      0x08,
                                      0x70,
                                      0x72,
                                      0x6F,
                                      0x2D,
                                      0x6C,
                                      0x69,
                                      0x74,
                                      0x65};

const uint8_t shared_info_data_buffer[] = {0x3c, 0x88, 0x10, 0x08, 0x70, 0x72,
                                           0x6F, 0x2D, 0x6C, 0x69, 0x74, 0x65};

#define SET_CERT_TLV_FIELD(cert, tag, val, length) \
  do {                                             \
    cert->lv_##tag.value = val;                    \
    cert->lv_##tag.len = length;                   \
  } while (0)

#define INIT_TLV_FIELD(tlv, tag_value, buf, buf_len) \
  do {                                               \
    tlv.tag = tag_value;                             \
    tlv.length = buf_len;                            \
    tlv.value = buf;                                 \
  } while (0)

bool scp11_get_pubkey(uint8_t *input, uint8_t inpue_len, uint8_t *pubkey) {
  uint8_t *p = input;
  uint8_t *end = input + inpue_len;
  uint16_t tag;
  uint16_t value_len = 0;
  uint16_t offset = 0;

  if (inpue_len == 0) {
    return false;
  }

  while (p < end) {
    if (!tlv_parse_tag(p, end, &tag, &offset)) {
      return false;
    }
    p += offset;

    if (!tlv_parse_length(p, end, &value_len, &offset)) {
      return false;
    }

    p += offset;

    switch (tag) {
      case GPC_TLV_PK_Q:
        if (value_len != 65) return false;
        memcpy(pubkey, p, value_len);
        break;
      case GPC_TLV_PK_PARAM:
        break;
      default:
        break;
    }
    p += value_len;
  }

  return true;
}

static bool scp11_get_signature(uint8_t *input, uint8_t inpue_len,
                                uint8_t *signature) {
  uint8_t *p = input;
  uint8_t *end = input + inpue_len;
  uint16_t value_len = 0;
  uint16_t offset = 0;

  if (inpue_len == 0) {
    return false;
  }

  // der signature
  if (*p != 0x30) {
    return false;
  }
  p++;

  if (!tlv_parse_length(p, end, &value_len, &offset)) {
    return false;
  }

  p += offset;

  for (int i = 0; i < 2; i++) {
    if (*p != 0x02) {
      return false;
    }
    p++;
    if (!tlv_parse_length(p, end, &value_len, &offset)) {
      return false;
    }
    p += offset;

    if (value_len == 33 && *p == 0x00) {
      p++;
      value_len--;
    }

    if (value_len != 32) {
      return false;
    }
    memcpy(signature + i * 32, p, value_len);
    p += value_len;
  }

  return true;
}

bool scp11_certificate_parse_and_verify(uint8_t *cert_raw, uint16_t cert_len,
                                        scp11_certificate *cert) {
  // Parse certificate
  uint16_t tag;
  uint8_t tag_len, len_len;
  uint16_t value_len = 0;
  uint16_t offset = 0;

  if (cert_len == 0) {
    return false;
  }

  uint8_t *p = cert_raw;
  uint8_t *end = cert_raw + cert_len;

  SHA256_CTX ctx = {0};
  uint8_t digest[32] = {0}, signature[64] = {0};
  sha256_Init(&ctx);

  while (p < end) {
    if (!tlv_parse_tag(p, end, &tag, &offset)) {
      return false;
    }
    p += offset;
    tag_len = offset;

    if (!tlv_parse_length(p, end, &value_len, &offset)) {
      return false;
    }

    p += offset;
    len_len = offset;

    bool is_nested = tag_len == 1 ? tag & 0x20 : (tag >> 8) & 0x20;

    if (is_nested) {
      switch (tag) {
        case GPC_TLV_SCP11CRT_ENTITY:
          SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_ENTITY, p, value_len);
          break;
        case GPC_TLV_SCP11CRT_PUBKEY:
          SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_PUBKEY, p, value_len);
          sha256_Update(&ctx, p - tag_len - len_len,
                        tag_len + len_len + value_len);
          p += value_len;
          break;
        case GPC_TLV_SCP11CRT_BF_RESTR:
          SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_BF_RESTR, p, value_len);
          sha256_Update(&ctx, p - tag_len - len_len,
                        tag_len + len_len + value_len);
          p += value_len;
          break;
        default:
          break;
      }

      continue;
    }

    switch (tag) {
      case GPC_TLV_SCP11CRT_SN:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_SN, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_CAKLOCID:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_CAKLOCID, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_SUBJECTID:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_SUBJECTID, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_KEYUSAGE:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_KEYUSAGE, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_EFFEDATE:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_EFFEDATE, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_EXPEDATE:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_EXPEDATE, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_DISC_53:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_DISC_53, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_DISC_73:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_DISC_73, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_BF_RESTR:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_BF_RESTR, p, value_len);
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
      case GPC_TLV_SCP11CRT_SIGNATURE:
        SET_CERT_TLV_FIELD(cert, GPC_TLV_SCP11CRT_SIGNATURE, p, value_len);
        break;
      default:
        sha256_Update(&ctx, p - tag_len - len_len,
                      tag_len + len_len + value_len);
        break;
    }
    p += value_len;
  }
  // Verify certificate
  sha256_Final(&ctx, digest);

  if (!scp11_get_signature(cert->lv_GPC_TLV_SCP11CRT_SIGNATURE.value,
                           cert->lv_GPC_TLV_SCP11CRT_SIGNATURE.len,
                           signature)) {
    return false;
  }

  return ecdsa_verify_digest(&nist256p1, sd_cert_verify_pubkey, signature,
                             digest) == 0;
}

bool scp11_get_mutual_auth_data(uint8_t *data, uint8_t *data_len,
                                scp11_context scp11_ctx) {
  uint8_t *p = data;

  uint8_t len = sizeof(shared_info_buffer) + 2 + 68;

  if (*data_len < len) {
    return false;
  }

  *p++ = GPC_TLV_MA_CR;
  *p++ = scp11_ctx.shared_info.len;
  memcpy(p, scp11_ctx.shared_info.value, scp11_ctx.shared_info.len);
  p += scp11_ctx.shared_info.len;
  *p++ = GPC_TLV_MA_PK >> 8;
  *p++ = GPC_TLV_MA_PK & 0xff;
  *p++ = 0x41;
  memcpy(p, scp11_ctx.mutual_auth.oce_temp_public_key, 65);
  p += 65;

  *data_len = len;

  return true;
}

bool scp11_parse_response_msg(scp11_response_msg *resp_msg) {
  uint8_t *p = resp_msg->data;
  uint8_t *end = resp_msg->data + resp_msg->data_len;
  uint16_t tag, value_len, offset;

  if (!tlv_parse_tag(p, end, &tag, &offset)) {
    return false;
  }

  if (tag != GPC_TLV_MA_PK) {
    return false;
  }
  p += offset;

  if (!tlv_parse_length(p, end, &value_len, &offset)) {
    return false;
  }
  p += offset;

  resp_msg->lv_GPC_TLV_MA_PK.value = p;
  resp_msg->lv_GPC_TLV_MA_PK.len = value_len;

  p += value_len;

  if (!tlv_parse_tag(p, end, &tag, &offset)) {
    return false;
  }
  p += offset;

  if (tag != GPC_TLV_MA_RECEIPT) {
    return false;
  }

  if (!tlv_parse_length(p, end, &value_len, &offset)) {
    return false;
  }
  p += offset;

  if (value_len != 16) {
    return false;
  }

  resp_msg->lv_GPC_TLV_MA_RECEIPT.value = p;
  resp_msg->lv_GPC_TLV_MA_RECEIPT.len = value_len;

  return true;
}

bool scp11_open_secure_channel(scp11_context *scp11_ctx) {
  uint8_t shsss_key[65], shses_key[65];
  uint8_t z[40] = {0};

  uint8_t counter[4] = {0x00, 0x00, 0x00, 0x01};

  if (!scp11_parse_response_msg(&scp11_ctx->response_msg)) {
    return false;
  }

  scp11_get_pubkey(scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_PUBKEY.value,
                   scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_PUBKEY.len,
                   scp11_ctx->mutual_auth.sd_public_key);

  //  use se
  if (0 !=
      se_lite_card_ecdh(scp11_ctx->mutual_auth.sd_public_key + 1, shsss_key)) {
    return false;
  }
  // if (0 != ecdh_multiply(&nist256p1, scp11_ctx->mutual_auth.oce_private_key,
  //                        scp11_ctx->mutual_auth.sd_public_key, shsss_key)) {
  //   return false;
  // }

  if (0 != ecdh_multiply(&nist256p1,
                         scp11_ctx->mutual_auth.oce_temp_private_key,
                         scp11_ctx->mutual_auth.sd_public_key, shses_key)) {
    return false;
  }

  sha1_Raw(shses_key + 1, 32, z);
  sha1_Raw(shsss_key + 1, 32, z + 20);

  SHA256_CTX ctx = {0};
  uint8_t digest[32];

  sha256_Init(&ctx);
  sha256_Update(&ctx, z, 40);
  sha256_Update(&ctx, counter, 4);
  sha256_Update(&ctx, shared_info_data_buffer, sizeof(shared_info_data_buffer));
  sha256_Update(&ctx, scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_CAKLOCID.value,
                scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_CAKLOCID.len);
  sha256_Final(&ctx, digest);

  memcpy(scp11_ctx->session_key.key_dek, digest, 16);
  memcpy(scp11_ctx->session_key.s_enc, digest + 16, 16);

  counter[3] = 0x02;
  sha256_Init(&ctx);
  sha256_Update(&ctx, z, 40);
  sha256_Update(&ctx, counter, 4);
  sha256_Update(&ctx, shared_info_data_buffer, sizeof(shared_info_data_buffer));
  sha256_Update(&ctx, scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_CAKLOCID.value,
                scp11_ctx->sd_cert.lv_GPC_TLV_SCP11CRT_CAKLOCID.len);
  sha256_Final(&ctx, digest);

  memcpy(scp11_ctx->session_key.s_mac, digest, 16);
  memcpy(scp11_ctx->session_key.s_rmac, digest + 16, 16);

  uint8_t mac_data[255], mac[16];
  uint8_t mac_data_len = sizeof(mac_data);

  scp11_get_mutual_auth_data(mac_data, &mac_data_len, *scp11_ctx);
  memcpy(mac_data + mac_data_len, scp11_ctx->response_msg.data, 68);
  mac_data_len += 68;

  AES128_CMAC(scp11_ctx->session_key.key_dek, mac_data, mac_data_len, mac);

  if (memcmp(mac, scp11_ctx->response_msg.lv_GPC_TLV_MA_RECEIPT.value, 16) !=
      0) {
    return false;
  }

  scp11_ctx->is_secure_channel_opened = true;

  return true;
}

void scp11_init(scp11_context *scp11_ctx) {
  memset(scp11_ctx, 0, sizeof(scp11_ctx));

  scp11_ctx->shared_info.value = (uint8_t *)shared_info_buffer;
  scp11_ctx->shared_info.len = sizeof(shared_info_buffer);

  memcpy(scp11_ctx->oce_cert.raw, device_certificate,
         sizeof(device_certificate) - 1);
  scp11_ctx->oce_cert.raw_len = sizeof(device_certificate) - 1;

  // private key stored in SE
  // memcpy(scp11_ctx->mutual_auth.oce_private_key, device_private_key, 32);

  scp11_ctx->response_msg.data_len = sizeof(scp11_ctx->response_msg.data);

  if (!scp11_certificate_parse_and_verify(scp11_ctx->oce_cert.raw,
                                          scp11_ctx->oce_cert.raw_len,
                                          &scp11_ctx->oce_cert)) {
    return;
  }

  scp11_get_pubkey(scp11_ctx->oce_cert.lv_GPC_TLV_SCP11CRT_PUBKEY.value,
                   scp11_ctx->oce_cert.lv_GPC_TLV_SCP11CRT_PUBKEY.len,
                   scp11_ctx->mutual_auth.oce_public_key);

  random_buffer(scp11_ctx->mutual_auth.oce_temp_private_key,
                sizeof(scp11_ctx->mutual_auth.oce_temp_private_key));

  ecdsa_get_public_key65(&nist256p1,
                         scp11_ctx->mutual_auth.oce_temp_private_key,
                         scp11_ctx->mutual_auth.oce_temp_public_key);
}

void scp11_close_secure_channel(scp11_context *scp11_ctx) {
  scp11_ctx->is_secure_channel_opened = false;
}

bool scp11_get_secure_channel_status(scp11_context *scp11_ctx) {
  return scp11_ctx->is_secure_channel_opened;
}
