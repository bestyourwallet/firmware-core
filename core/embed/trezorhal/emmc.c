#include STM32_HAL_H

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "common.h"
#include "emmc.h"

#if (SDMMC_DEVICE == EMMC)
static MMC_HandleTypeDef hmmc1;
#else
static SD_HandleTypeDef hsd1;
#endif

#define EMMC 0
#define SD 1
#define SDMMC_DEVICE EMMC

#define EMMC_EXT_CSD_CMD_SET_NORMAL 0
#define EMMC_EXT_CSD_PRE_EOL_INFO 267U
#define EMMC_EXT_CSD_DEVICE_LIFE_TIME_EST_TYP_A 268U
#define EMMC_EXT_CSD_DEVICE_LIFE_TIME_EST_TYP_B 269U

static bool emmc_wait_ready(uint32_t timeout) {
  uint32_t tickstart = HAL_GetTick();
  while (emmc_get_card_state() != MMC_TRANSFER_OK) {
    if (((HAL_GetTick() - tickstart) > timeout) || (timeout == 0U)) {
      return false;
    }
  }
  return true;
}

static bool emmc_ext_csd_switch_to_block_mode(void) {
  if (SDMMC_CmdBlockLength(hmmc1.Instance, EMMC_EXT_CSD_SIZE) != HAL_OK) {
    return false;
  }
  return true;
}

void emmc_init(void) {
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* Peripheral clock enable */
  __HAL_RCC_SDMMC1_CLK_ENABLE();

  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  /**SDMMC1 GPIO Configuration
  PC12    ------> SDMMC1_CK
  PD2     ------> SDMMC1_CMD
  PC8     ------> SDMMC1_D0
  PC9     ------> SDMMC1_D1
  PC10    ------> SDMMC1_D2
  PC11    ------> SDMMC1_D3
  PB8     ------> SDMMC1_D4
  PB9     ------> SDMMC1_D5
  PC6     ------> SDMMC1_D6
  PC7     ------> SDMMC1_D7
  */
  GPIO_InitStruct.Pin = GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_8 |
                        GPIO_PIN_9 | GPIO_PIN_7 | GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF12_SDIO1;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = GPIO_PIN_9 | GPIO_PIN_8;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF12_SDIO1;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = GPIO_PIN_2;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF12_SDIO1;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  hmmc1.Instance = SDMMC1;
  hmmc1.Init.ClockEdge = SDMMC_CLOCK_EDGE_RISING;
  hmmc1.Init.ClockPowerSave = SDMMC_CLOCK_POWER_SAVE_DISABLE;
  hmmc1.Init.BusWide = SDMMC_BUS_WIDE_8B;
  hmmc1.Init.HardwareFlowControl = SDMMC_HARDWARE_FLOW_CONTROL_ENABLE;
  hmmc1.Init.ClockDiv = 2;
#if (SDMMC_DEVICE == EMMC)
  if (HAL_MMC_Init(&hmmc1) != HAL_OK) {
    ensure(0, "mmc init fail");
  }

  if (HAL_MMC_ConfigWideBusOperation(&hmmc1, SDMMC_BUS_WIDE_8B) != HAL_OK) {
    ensure(0, "mmc wide set fail");
  }

  if (HAL_MMC_ConfigSpeedBusOperation(&hmmc1, SDMMC_SPEED_MODE_DDR) != HAL_OK) {
    ensure(0, "mmc speed set fail");
  }
#else
  if (HAL_SD_Init(&hsd1) != HAL_OK) {
    ensure(0, "sd init fail");
  }
#endif
}

void emmc_deinit() {
  // deinit
#if (SDMMC_DEVICE == EMMC)
  if (HAL_MMC_DeInit(&hmmc1) != HAL_OK) {
    ensure(0, "mmc deinit fail");
  }
#else
  if (HAL_SD_DeInit(&hsd1) != HAL_OK) {
    ensure(0, "sd deinit fail");
  }
#endif

  // reset and close clock
  __HAL_RCC_SDMMC1_FORCE_RESET();
  __HAL_RCC_SDMMC1_RELEASE_RESET();
  __HAL_RCC_SDMMC1_CLK_DISABLE();

  // release gpios
  HAL_GPIO_DeInit(GPIOC, GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_8 |
                             GPIO_PIN_9 | GPIO_PIN_7 | GPIO_PIN_6);
  HAL_GPIO_DeInit(GPIOB, GPIO_PIN_9 | GPIO_PIN_8);
  HAL_GPIO_DeInit(GPIOD, GPIO_PIN_2);
}

uint8_t emmc_get_card_state(void) {
#if (SDMMC_DEVICE == EMMC)
  return ((HAL_MMC_GetCardState(&hmmc1) == HAL_MMC_CARD_TRANSFER)
              ? MMC_TRANSFER_OK
              : MMC_TRANSFER_BUSY);
#else
  return ((HAL_SD_GetCardState(&hsd1) == HAL_SD_CARD_TRANSFER)
              ? MMC_TRANSFER_OK
              : MMC_TRANSFER_BUSY);
#endif
}

void emmc_get_card_info(EMMC_CardInfoTypeDef* card_info) {
#if SDMMC_DEVICE == EMMC
  if (HAL_MMC_GetCardInfo(&hmmc1, card_info) == HAL_OK) {
  }
#else
  HAL_SD_CardInfoTypeDef sd_info;
  if (HAL_SD_GetCardInfo(&hsd1, &sd_info) == HAL_OK) {
    card_info->RelCardAdd = sd_info.RelCardAdd;
    card_info->BlockNbr = sd_info.BlockNbr;
    card_info->BlockSize = sd_info.BlockSize;
    card_info->LogBlockNbr = sd_info.LogBlockNbr;
    card_info->LogBlockSize = sd_info.LogBlockSize;
  }
#endif
}

uint8_t emmc_read_blocks(uint8_t* data, uint32_t address, uint32_t nums,
                         uint32_t timeout) {
  HAL_StatusTypeDef state;
#if (SDMMC_DEVICE == EMMC)
  state = HAL_MMC_ReadBlocks(&hmmc1, data, address, nums, timeout);
#else
  state = HAL_SD_ReadBlocks(&hsd1, data, address, nums, timeout);
#endif
  if (state == HAL_OK) {
    if (!emmc_wait_ready(timeout)) {
      return MMC_ERROR;
    }
    return MMC_OK;
  } else {
    return MMC_ERROR;
  }
}

uint8_t emmc_write_blocks(uint8_t* data, uint32_t address, uint32_t nums,
                          uint32_t timeout) {
  HAL_StatusTypeDef state;
#if (SDMMC_DEVICE == EMMC)
  state = HAL_MMC_WriteBlocks(&hmmc1, data, address, nums, timeout);
#else
  state = HAL_SD_WriteBlocks(&hsd1, data, address, nums, timeout);
#endif
  if (state == HAL_OK) {
    if (!emmc_wait_ready(timeout)) {
      return MMC_ERROR;
    }
    return MMC_OK;
  } else {
    return MMC_ERROR;
  }
}

uint8_t emmc_read_blocks_dma(uint8_t* data, uint32_t address, uint32_t nums,
                             uint32_t timeout) {
  if (HAL_MMC_ReadBlocks_DMA(&hmmc1, data, address, nums) == HAL_OK) {
    if (timeout == HAL_MAX_DELAY) {
      while (emmc_get_card_state() != MMC_TRANSFER_OK) {
      }
    } else if (!emmc_wait_ready(timeout)) {
      return MMC_ERROR;
    }
    return MMC_OK;
  } else {
    return MMC_ERROR;
  }
}

uint8_t emmc_write_blocks_dma(uint8_t* data, uint32_t address, uint32_t nums,
                              uint32_t timeout) {
  if (HAL_MMC_WriteBlocks_DMA(&hmmc1, data, address, nums) == HAL_OK) {
    return MMC_OK;
  } else {
    return MMC_ERROR;
  }
}

uint8_t emmc_erase(uint32_t start_address, uint32_t end_address) {
  if (HAL_MMC_Erase(&hmmc1, start_address, end_address) == HAL_OK) {
    if (!emmc_wait_ready(EMMC_TIMEOUT)) {
      return MMC_ERROR;
    }
    return MMC_OK;
  }
  return MMC_ERROR;
}

uint64_t emmc_get_capacity_in_bytes(void) {
  EMMC_CardInfoTypeDef card_info = {0};
  emmc_get_card_info(&card_info);
  return (uint64_t)card_info.LogBlockNbr * card_info.LogBlockSize;
}

bool emmc_read_ext_csd(uint8_t* ext_csd, uint32_t timeout) {
#if (SDMMC_DEVICE != EMMC)
  (void)ext_csd;
  (void)timeout;
  return false;
#else
  SDMMC_DataInitTypeDef config;
  uint32_t errorstate;
  uint32_t tickstart = HAL_GetTick();
  uint32_t i = 0;

  if (ext_csd == NULL) {
    return false;
  }

  memset(ext_csd, 0, EMMC_EXT_CSD_SIZE);

  hmmc1.ErrorCode = HAL_MMC_ERROR_NONE;
  hmmc1.Instance->DCTRL = 0;

  config.DataTimeOut = SDMMC_DATATIMEOUT;
  config.DataLength = 0;
  config.DataBlockSize = SDMMC_DATABLOCK_SIZE_1B;
  config.TransferDir = SDMMC_TRANSFER_DIR_TO_SDMMC;
  config.TransferMode = SDMMC_TRANSFER_MODE_BLOCK;
  config.DPSM = SDMMC_DPSM_DISABLE;
  (void)SDMMC_ConfigData(hmmc1.Instance, &config);

  if (!emmc_ext_csd_switch_to_block_mode()) {
    __HAL_MMC_CLEAR_FLAG(&hmmc1, SDMMC_STATIC_FLAGS);
    hmmc1.State = HAL_MMC_STATE_READY;
    return false;
  }

  config.DataTimeOut = SDMMC_DATATIMEOUT;
  config.DataLength = EMMC_EXT_CSD_SIZE;
  config.DataBlockSize = SDMMC_DATABLOCK_SIZE_512B;
  config.TransferDir = SDMMC_TRANSFER_DIR_TO_SDMMC;
  config.TransferMode = SDMMC_TRANSFER_MODE_BLOCK;
  config.DPSM = SDMMC_DPSM_ENABLE;
  (void)SDMMC_ConfigData(hmmc1.Instance, &config);

  errorstate = SDMMC_CmdSendEXTCSD(hmmc1.Instance, EMMC_EXT_CSD_CMD_SET_NORMAL);
  if (errorstate != HAL_MMC_ERROR_NONE) {
    __HAL_MMC_CLEAR_FLAG(&hmmc1, SDMMC_STATIC_FLAGS);
    hmmc1.ErrorCode |= errorstate;
    hmmc1.State = HAL_MMC_STATE_READY;
    return false;
  }

  while (!__HAL_MMC_GET_FLAG(&hmmc1, SDMMC_FLAG_RXOVERR | SDMMC_FLAG_DCRCFAIL |
                                         SDMMC_FLAG_DTIMEOUT |
                                         SDMMC_FLAG_DATAEND)) {
    if (__HAL_MMC_GET_FLAG(&hmmc1, SDMMC_FLAG_RXFIFOHF)) {
      for (uint32_t count = 0; count < 8U; count++) {
        uint32_t tmp_data = SDMMC_ReadFIFO(hmmc1.Instance);
        if ((i * 4U) < EMMC_EXT_CSD_SIZE) {
          ext_csd[i * 4U] = (uint8_t)(tmp_data & 0xFFU);
          ext_csd[i * 4U + 1U] = (uint8_t)((tmp_data >> 8U) & 0xFFU);
          ext_csd[i * 4U + 2U] = (uint8_t)((tmp_data >> 16U) & 0xFFU);
          ext_csd[i * 4U + 3U] = (uint8_t)((tmp_data >> 24U) & 0xFFU);
        }
        i++;
      }
    }

    if (((HAL_GetTick() - tickstart) >= timeout) || (timeout == 0U)) {
      __HAL_MMC_CLEAR_FLAG(&hmmc1, SDMMC_STATIC_FLAGS);
      hmmc1.ErrorCode |= HAL_MMC_ERROR_TIMEOUT;
      hmmc1.State = HAL_MMC_STATE_READY;
      return false;
    }
  }

  if (__HAL_MMC_GET_FLAG(&hmmc1, SDMMC_FLAG_RXOVERR | SDMMC_FLAG_DCRCFAIL |
                                     SDMMC_FLAG_DTIMEOUT)) {
    __HAL_MMC_CLEAR_FLAG(&hmmc1, SDMMC_STATIC_FLAGS);
    hmmc1.ErrorCode |= HAL_MMC_ERROR_DATA_CRC_FAIL;
    hmmc1.State = HAL_MMC_STATE_READY;
    return false;
  }

  errorstate = SDMMC_CmdSendStatus(
      hmmc1.Instance, (uint32_t)(((uint32_t)hmmc1.MmcCard.RelCardAdd) << 16));
  if (errorstate != HAL_MMC_ERROR_NONE) {
    hmmc1.ErrorCode |= errorstate;
  }

  __HAL_MMC_CLEAR_FLAG(&hmmc1, SDMMC_STATIC_DATA_FLAGS);
  hmmc1.State = HAL_MMC_STATE_READY;

  return hmmc1.ErrorCode == HAL_MMC_ERROR_NONE;
#endif
}

bool emmc_get_lifetime_info(char* buf, size_t buf_len) {
  uint8_t ext_csd[EMMC_EXT_CSD_SIZE] = {0};

  if (buf == NULL || buf_len == 0) {
    return false;
  }

  if (!emmc_read_ext_csd(ext_csd, EMMC_TIMEOUT)) {
    return false;
  }

  int written = snprintf(
      buf, buf_len,
      "Warning: This file was generated by the boardloader during the first "
      "eMMC initialization.\n"
      "PRE_EOL_INFO=0x%02X\n"
      "DEVICE_LIFE_TIME_EST_TYP_A=0x%02X\n"
      "DEVICE_LIFE_TIME_EST_TYP_B=0x%02X\n",
      ext_csd[EMMC_EXT_CSD_PRE_EOL_INFO],
      ext_csd[EMMC_EXT_CSD_DEVICE_LIFE_TIME_EST_TYP_A],
      ext_csd[EMMC_EXT_CSD_DEVICE_LIFE_TIME_EST_TYP_B]);

  return written > 0 && (size_t)written < buf_len;
}

void emmc_test(void) {
  uint8_t buf[512];
  for (int i = 0; i < 512; i++) {
    buf[i] = i;
  }
  emmc_write_blocks(buf, 0, 1, 500);
  memset(buf, 0x00, 512);
  emmc_read_blocks(buf, 0, 1, 500);
  for (int i = 0; i < 512; i++) {
    // display_printf(" %X\n", buf[i]);
  }
}
