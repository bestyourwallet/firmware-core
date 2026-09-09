#ifndef _TREZORHAL_SE_H_
#define _TREZORHAL_SE_H_

#include <stdbool.h>
#include "secbool.h"

#define SE_1ST_ADDRESS (0x50 << 1)

#define SE_MASTER_ADDRESS SE_1ST_ADDRESS

extern int se_irq_nest;

void se_io_init(void);
void se_init(void);
void se_power_up(bool up);
void se_reset(void);
secbool se_transmit(uint8_t* cmd, uint16_t len, uint8_t* resp,
                    uint16_t* resp_len);
secbool se_fp_transmit(uint8_t* cmd, uint16_t len, uint8_t* resp,
                       uint16_t* resp_len);
secbool se_transmit_ex(uint8_t addr, uint8_t* cmd, uint16_t len, uint8_t* resp,
                       uint16_t* resp_len);
uint16_t se_last_error();

int se_master_send(uint8_t* cmd, uint16_t len);
int se_master_recv(uint8_t* resp, uint16_t* resp_len);

#endif
