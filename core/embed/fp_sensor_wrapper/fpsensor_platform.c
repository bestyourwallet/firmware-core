#include "fpsensor_platform.h"

#include <stdio.h>
#include <string.h>

#include "common.h"
#include "fpalgorithm_interface.h"
#include "se_acl16.h"
#include STM32_HAL_H
#include "irq.h"
#include "systick.h"
#include "tlsf.h"

SPI_HandleTypeDef spi_fp = {0};

// @formatter:off
// clang-format off

// spi cs pin
#define FP_CS_GPIO_PORT     GPIOA
#define FP_CS_PIN           GPIO_PIN_15
// fp irq pin
#define FP_IRQ_GPIO_PORT    GPIOB
#define FP_IRQ_PIN          GPIO_PIN_15
// fp reset pin
#define FP_RST_PORT         GPIOB
#define FP_RST_PIN          GPIO_PIN_14
// fp power pin
#define FP_POWER_PORT       GPIOB
#define FP_POWER_PIN        GPIO_PIN_2

#define MAX_MEMORY_SIZE (1024U * 100U)
static bool fp_touched = false;
static uint8_t image_buf[FP_ALGORITHM_IMAGE_SIZE]
    __attribute__((section(".exram")));
static uint8_t memory_buf[MAX_MEMORY_SIZE] __attribute__((section(".exram")));
static uint8_t ram_flash[FP_ALGORITHM_WORKSPACE_SIZE]
    __attribute__((section(".exram")));
static uint8_t template_buf[FP_ALGORITHM_TEMPLATE_SIZE]
    __attribute__((section(".exram")));
static tlsf_t sdram_tlsf;

#define FP_TEMPLATE_STORE_HEAD_OFFSET       0U
#define FP_TEMPLATE_STORE_HEAD_SIZE         512U
#define FP_TEMPLATE_STORE_GLOBAL_HEAD_SIZE  32U
#define FP_TEMPLATE_STORE_SLOT_META_SIZE    32U
#define FP_TEMPLATE_STORE_SLOT_COUNT        FP_ALGORITHM_MAX_TEMPLATE_COUNT
#define FP_TEMPLATE_STORE_SLOT_DATA_SIZE    FP_ALGORITHM_TEMPLATE_SIZE
#define FP_TEMPLATE_STORE_DATA_START_OFFSET (FP_TEMPLATE_STORE_HEAD_OFFSET + FP_TEMPLATE_STORE_HEAD_SIZE)

#define FP_TEMPLATE_STORE_GLOBAL_MAGIC      0x46505345U
#define FP_TEMPLATE_STORE_SLOT_MAGIC        0x4650534CU
#define FP_TEMPLATE_STORE_FORMAT_VERSION    1U
#define FP_TEMPLATE_STORE_VALID_MARK        0x4650564CU
#define FP_TEMPLATE_STORE_NOT_DELETED_MARK  0x46504E44U
#define FP_TEMPLATE_STORE_DELETED_MARK      0x46504445U

typedef struct
{
    uint32_t magic;
    uint32_t version;
    uint32_t slot_count;
    uint32_t slot_size;
    uint32_t head_size;
    uint32_t data_start_offset;
    uint32_t reserved[2];
} fp_template_global_head_t;

typedef struct
{
    uint32_t magic;
    uint32_t version;
    uint32_t template_id;
    uint32_t template_type;
    uint32_t template_len;
    uint32_t crc32;
    uint32_t valid_marker;
    uint32_t delete_marker;
} fp_template_slot_meta_t;

typedef char fp_template_global_head_size_must_be_32
    [(sizeof(fp_template_global_head_t) == FP_TEMPLATE_STORE_GLOBAL_HEAD_SIZE) ? 1 : -1];
typedef char fp_template_slot_meta_size_must_be_32
    [(sizeof(fp_template_slot_meta_t) == FP_TEMPLATE_STORE_SLOT_META_SIZE) ? 1 : -1];

#define logDebug(fmt, ...)                                                            \
  do                                                                                  \
  {                                                                                   \
    printf("[DEBUG:%s line:%d]\t" fmt "\r\n", __FUNCTION__, __LINE__, ##__VA_ARGS__); \
  }                                                                                   \
  while ( 0 )

// @formatter:on

static uint32_t fp_align4(uint32_t len)
{
    return (len + 3U) & ~3U;
}

static uint32_t fp_template_store_slot_meta_offset(uint8_t slot)
{
    return FP_TEMPLATE_STORE_HEAD_OFFSET + FP_TEMPLATE_STORE_GLOBAL_HEAD_SIZE +
           (uint32_t)slot * FP_TEMPLATE_STORE_SLOT_META_SIZE;
}

static uint32_t fp_template_store_slot_data_offset(uint8_t slot)
{
    return FP_TEMPLATE_STORE_DATA_START_OFFSET + (uint32_t)slot * FP_TEMPLATE_STORE_SLOT_DATA_SIZE;
}

static uint32_t fp_template_store_crc32(const uint8_t* data, uint32_t len)
{
    uint32_t crc = 0xFFFFFFFFU;
    for ( uint32_t i = 0; i < len; i++ )
    {
        crc ^= data[i];
        for ( uint8_t bit = 0; bit < 8; bit++ )
        {
            uint32_t mask = 0U - (crc & 1U);
            crc = (crc >> 1) ^ (0xEDB88320U & mask);
        }
    }
    return crc ^ 0xFFFFFFFFU;
}

static bool fp_template_store_read_aligned(uint32_t offset, void* data, uint32_t len)
{
    if ( ((offset | len) & 0x03U) != 0U )
    {
        return false;
    }
    return se_fp_read(offset, data, len, 0, 1);
}

static bool fp_template_store_write_aligned(uint32_t offset, const void* data, uint32_t len)
{
    if ( ((offset | len) & 0x03U) != 0U )
    {
        return false;
    }
    return se_fp_write(offset, data, len, 0, 1);
}

static void fp_template_store_fill_global_head(fp_template_global_head_t* head)
{
    memset(head, 0, sizeof(*head));
    head->magic = FP_TEMPLATE_STORE_GLOBAL_MAGIC;
    head->version = FP_TEMPLATE_STORE_FORMAT_VERSION;
    head->slot_count = FP_TEMPLATE_STORE_SLOT_COUNT;
    head->slot_size = FP_TEMPLATE_STORE_SLOT_DATA_SIZE;
    head->head_size = FP_TEMPLATE_STORE_HEAD_SIZE;
    head->data_start_offset = FP_TEMPLATE_STORE_DATA_START_OFFSET;
}

static bool fp_template_store_global_head_is_valid(const fp_template_global_head_t* head)
{
    return head->magic == FP_TEMPLATE_STORE_GLOBAL_MAGIC &&
           head->version == FP_TEMPLATE_STORE_FORMAT_VERSION &&
           head->slot_count == FP_TEMPLATE_STORE_SLOT_COUNT &&
           head->slot_size == FP_TEMPLATE_STORE_SLOT_DATA_SIZE &&
           head->head_size == FP_TEMPLATE_STORE_HEAD_SIZE &&
           head->data_start_offset == FP_TEMPLATE_STORE_DATA_START_OFFSET;
}

static int fp_template_store_read_global_head(fp_template_global_head_t* head)
{
    memset(head, 0, sizeof(*head));
    return fp_template_store_read_aligned(FP_TEMPLATE_STORE_HEAD_OFFSET, head, sizeof(*head)) ? 0 : -1;
}

static int fp_template_store_ensure_global_head(void)
{
    fp_template_global_head_t head = {0};
    if ( fp_template_store_read_global_head(&head) == 0 &&
         fp_template_store_global_head_is_valid(&head) )
    {
        return 0;
    }

    fp_template_store_fill_global_head(&head);
    return fp_template_store_write_aligned(FP_TEMPLATE_STORE_HEAD_OFFSET, &head, sizeof(head)) ? 0 : -1;
}

static int fp_template_store_read_slot_meta(uint8_t slot, fp_template_slot_meta_t* meta)
{
    if ( slot >= FP_TEMPLATE_STORE_SLOT_COUNT )
    {
        return -1;
    }
    memset(meta, 0, sizeof(*meta));
    if ( fp_template_store_read_aligned(fp_template_store_slot_meta_offset(slot), meta, sizeof(*meta)) )
    {
        return 0;
    }
    return -1;
}

static int fp_template_store_write_slot_meta(uint8_t slot, const fp_template_slot_meta_t* meta)
{
    if ( slot >= FP_TEMPLATE_STORE_SLOT_COUNT )
    {
        return -1;
    }
    return fp_template_store_write_aligned(fp_template_store_slot_meta_offset(slot), meta, sizeof(*meta)) ? 0 : -1;
}

static bool fp_template_store_slot_meta_is_active(const fp_template_slot_meta_t* meta)
{
    return meta->magic == FP_TEMPLATE_STORE_SLOT_MAGIC && meta->version == FP_TEMPLATE_STORE_FORMAT_VERSION &&
           meta->valid_marker == FP_TEMPLATE_STORE_VALID_MARK &&
           meta->delete_marker == FP_TEMPLATE_STORE_NOT_DELETED_MARK;
}

static bool fp_template_store_slot_meta_is_deleted(const fp_template_slot_meta_t* meta)
{
    return meta->magic == FP_TEMPLATE_STORE_SLOT_MAGIC && meta->version == FP_TEMPLATE_STORE_FORMAT_VERSION &&
           meta->valid_marker == FP_TEMPLATE_STORE_VALID_MARK &&
           meta->delete_marker == FP_TEMPLATE_STORE_DELETED_MARK;
}

static int fp_template_store_max_template_count(void)
{
    return FP_TEMPLATE_STORE_SLOT_COUNT;
}

static int fp_template_store_find_slot_for_template(uint16_t id, uint8_t* slot)
{
    int first_empty_slot = -1;
    int first_deleted_slot = -1;

    for ( uint8_t i = 0; i < FP_TEMPLATE_STORE_SLOT_COUNT; i++ )
    {
        fp_template_slot_meta_t meta = {0};
        if ( fp_template_store_read_slot_meta(i, &meta) != 0 )
        {
            return -1;
        }

        if ( (fp_template_store_slot_meta_is_active(&meta) || fp_template_store_slot_meta_is_deleted(&meta)) &&
             meta.template_id == id )
        {
            *slot = i;
            return 0;
        }
        if ( meta.magic != FP_TEMPLATE_STORE_SLOT_MAGIC || meta.version != FP_TEMPLATE_STORE_FORMAT_VERSION ||
             meta.valid_marker != FP_TEMPLATE_STORE_VALID_MARK ||
             (meta.delete_marker != FP_TEMPLATE_STORE_NOT_DELETED_MARK &&
              meta.delete_marker != FP_TEMPLATE_STORE_DELETED_MARK) )
        {
            if ( first_empty_slot < 0 )
            {
                first_empty_slot = i;
            }
            continue;
        }
        if ( fp_template_store_slot_meta_is_deleted(&meta) && first_deleted_slot < 0 )
        {
            first_deleted_slot = i;
        }
    }

    if ( first_empty_slot >= 0 )
    {
        *slot = (uint8_t)first_empty_slot;
        return 0;
    }
    if ( first_deleted_slot >= 0 )
    {
        *slot = (uint8_t)first_deleted_slot;
        return 0;
    }
    return -1;
}

static int tlsf_heap_init(void)
{
    memset(memory_buf, 0, MAX_MEMORY_SIZE);
    memset(ram_flash, 0, sizeof(ram_flash));
    sdram_tlsf = tlsf_create_with_pool(memory_buf, MAX_MEMORY_SIZE);
    return sdram_tlsf == NULL ? -1 : 0;
}

int fp_spi_init()
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    RCC_PeriphCLKInitTypeDef PeriphClkInitStruct = {0};

    PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_SPI3;
    PeriphClkInitStruct.Spi123ClockSelection = RCC_SPI123CLKSOURCE_PLL;
    if ( HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK ) {}

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    // SPI

    // // SPI_MISO    SPI3_MISO   PB4  AF6
    // GPIO_InitStruct.Pin = GPIO_PIN_4;
    // GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    // GPIO_InitStruct.Pull = GPIO_NOPULL;
    // GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    // GPIO_InitStruct.Alternate = GPIO_AF6_SPI3;
    // HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
    //
    // // SPI_MOSI    SPI3_MOSI   PD6  AF5
    // GPIO_InitStruct.Pin = GPIO_PIN_6;
    // GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    // GPIO_InitStruct.Pull = GPIO_NOPULL;
    // GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    // GPIO_InitStruct.Alternate = GPIO_AF5_SPI3;
    // HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);
    //
    // // SPI_CLK     SPI3_SCK    PB3  AF6
    // GPIO_InitStruct.Pin = GPIO_PIN_3;
    // GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    // GPIO_InitStruct.Pull = GPIO_NOPULL;
    // GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    // GPIO_InitStruct.Alternate = GPIO_AF6_SPI3;
    // HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    /**
     *  SPI3 GPIO Configuration
     *  PB4 (NJTRST)        ------> SPI3_MISO
     *  PD6                 ------> SPI3_MOSI
     *  PB3 (JTDO/TRACESWO) ------> SPI3_SCK
     */

    GPIO_InitStruct.Pin = GPIO_PIN_3;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Alternate = GPIO_AF6_SPI3;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_4;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Alternate = GPIO_AF6_SPI3;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_6;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Alternate = GPIO_AF5_SPI3;
    HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

    // SPI_CSn     SPI3_NSS    PA15 AF6
    GPIO_InitStruct.Pin = GPIO_PIN_15;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Alternate = 0;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_15, GPIO_PIN_SET);

    __HAL_RCC_SPI3_CLK_ENABLE();
    __HAL_RCC_SPI3_FORCE_RESET();
    __HAL_RCC_SPI3_RELEASE_RESET();

    spi_fp.Instance = SPI3;
    //     spi_fp.Init.Mode = SPI_MODE_MASTER;
    //     spi_fp.Init.Direction = SPI_DIRECTION_2LINES;
    //     spi_fp.Init.DataSize = SPI_DATASIZE_8BIT;
    //     spi_fp.Init.CLKPolarity = SPI_POLARITY_LOW;
    //     spi_fp.Init.CLKPhase = SPI_PHASE_1EDGE;
    // #ifdef SPI_FP_USE_HW_CS
    //     spi_fp.Init.NSS = SPI_NSS_HARD_OUTPUT;
    //     spi_fp.Init.NSSPolarity = SPI_NSS_POLARITY_LOW;
    //     spi_fp.Init.NSSPMode = SPI_NSS_PULSE_DISABLE;
    // #else
    //     spi_fp.Init.NSS = SPI_NSS_SOFT;
    // #endif
    //     spi_fp.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_64;
    //     spi_fp.Init.FirstBit = SPI_FIRSTBIT_MSB;
    //     spi_fp.Init.TIMode = SPI_TIMODE_DISABLE;
    //     spi_fp.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    spi_fp.Instance = SPI3;
    spi_fp.Init.Mode = SPI_MODE_MASTER;
    spi_fp.Init.Direction = SPI_DIRECTION_2LINES;
    spi_fp.Init.DataSize = SPI_DATASIZE_8BIT;
    spi_fp.Init.CLKPolarity = SPI_POLARITY_LOW;
    spi_fp.Init.CLKPhase = SPI_PHASE_1EDGE;
    spi_fp.Init.NSS = SPI_NSS_SOFT;
    spi_fp.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_128;
    spi_fp.Init.FirstBit = SPI_FIRSTBIT_MSB;
    spi_fp.Init.TIMode = SPI_TIMODE_DISABLE;
    spi_fp.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    spi_fp.Init.CRCPolynomial = 0x0;
    spi_fp.Init.NSSPMode = SPI_NSS_PULSE_ENABLE;
    spi_fp.Init.NSSPolarity = SPI_NSS_POLARITY_LOW;
    spi_fp.Init.FifoThreshold = SPI_FIFO_THRESHOLD_01DATA;
    spi_fp.Init.TxCRCInitializationPattern = SPI_CRC_INITIALIZATION_ALL_ZERO_PATTERN;
    spi_fp.Init.RxCRCInitializationPattern = SPI_CRC_INITIALIZATION_ALL_ZERO_PATTERN;
    spi_fp.Init.MasterSSIdleness = SPI_MASTER_SS_IDLENESS_00CYCLE;
    spi_fp.Init.MasterInterDataIdleness = SPI_MASTER_INTERDATA_IDLENESS_00CYCLE;
    spi_fp.Init.MasterReceiverAutoSusp = SPI_MASTER_RX_AUTOSUSP_DISABLE;
    spi_fp.Init.MasterKeepIOState = SPI_MASTER_KEEP_IO_STATE_DISABLE;
    spi_fp.Init.IOSwap = SPI_IO_SWAP_DISABLE;

    if ( HAL_OK != HAL_SPI_Init(&spi_fp) )
    {
        return -1;
    }

    return 0;
}

int fp_gpio_init()
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    // MISC

    // SPI_INT     FP_IRQ      PB15
    GPIO_InitStruct.Pin = GPIO_PIN_15;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = 0; // ignored
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    // RSTn        FP_RST      PB14
    GPIO_InitStruct.Pin = GPIO_PIN_14;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = 0; // ignored
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET);

    NVIC_SetPriority(EXTI15_10_IRQn, IRQ_PRI_GPIO);
    return 0;
}

void fpsensor_state_set(bool state)
{
    fp_touched = state;
}

int fpsensor_detect(void)
{
    if ( fp_touched )
    {
        fp_touched = false;
        return 1;
    }
    return 0;
}

void fpsensor_irq_enable(void)
{
    fp_touched = false;

    EXTI_HandleTypeDef hexti = {0};
    EXTI_ConfigTypeDef pExtiConfig;
    pExtiConfig.Line = EXTI_LINE_15;
    pExtiConfig.Mode = EXTI_MODE_INTERRUPT;
    pExtiConfig.Trigger = EXTI_TRIGGER_RISING;
    pExtiConfig.GPIOSel = EXTI_GPIOB;
    HAL_EXTI_SetConfigLine(&hexti, &pExtiConfig);
}

void fpsensor_irq_disable(void)
{
    __HAL_GPIO_EXTI_CLEAR_IT(GPIO_PIN_15);
    EXTI_HandleTypeDef hexti = {0};
    EXTI_ConfigTypeDef pExtiConfig;
    pExtiConfig.Line = EXTI_LINE_15;
    pExtiConfig.Mode = EXTI_MODE_NONE;
    pExtiConfig.GPIOSel = EXTI_GPIOB;
    HAL_EXTI_SetConfigLine(&hexti, &pExtiConfig);
}

static int fp_send_byte(uint8_t value)
{
    return HAL_SPI_Transmit(&spi_fp, &value, 1, HAL_MAX_DELAY) == HAL_OK ? 0 : -1;
}

static int fp_recv_buffer(uint8_t* rx_buffer, uint32_t length)
{
    if ( rx_buffer == NULL || length == 0U )
    {
        return -1;
    }
    return HAL_SPI_Receive(&spi_fp, rx_buffer, length, HAL_MAX_DELAY) == HAL_OK ? 0 : -1;
}

static void fp_rstn_set(uint8_t level)
{
    if ( level == 1U )
    {
        HAL_GPIO_WritePin(FP_RST_PORT, FP_RST_PIN, GPIO_PIN_SET);
    }
    else
    {
        HAL_GPIO_WritePin(FP_RST_PORT, FP_RST_PIN, GPIO_PIN_RESET);
    }
}

static void fp_cs_set(uint8_t level)
{
    if ( level == 1U )
    {
        HAL_GPIO_WritePin(FP_CS_GPIO_PORT, FP_CS_PIN, GPIO_PIN_SET);
    }
    else
    {
        HAL_GPIO_WritePin(FP_CS_GPIO_PORT, FP_CS_PIN, GPIO_PIN_RESET);
    }
}

static void fp_delay_ms(uint32_t ms)
{
    dwt_delay_ms(ms);
}

static void fp_delay_us(uint32_t us)
{
    dwt_delay_us(us);
}

static void* fp_allocate(size_t size)
{
    return tlsf_malloc(sdram_tlsf, size);
}

static void fp_release(void* buffer)
{
    if ( buffer != NULL )
    {
        tlsf_free(sdram_tlsf, buffer);
    }
}

static bool fp_flash_range_is_valid(uint32_t address, uint32_t length)
{
    uintptr_t ram_start = (uintptr_t)ram_flash;
    uintptr_t current = (uintptr_t)address;
    if ( current < ram_start || length > sizeof(ram_flash) )
    {
        return false;
    }
    return current - ram_start <= sizeof(ram_flash) - length;
}

static int fp_flash_write(uint32_t address, const uint8_t* data, uint32_t length)
{
    if ( data == NULL || !fp_flash_range_is_valid(address, length) )
    {
        return -1;
    }
    memcpy((void*)(uintptr_t)address, data, length);
    return 0;
}

static int fp_flash_read(uint32_t address, uint32_t length, void* buffer)
{
    if ( buffer == NULL || !fp_flash_range_is_valid(address, length) )
    {
        return -1;
    }
    memcpy(buffer, (const void*)(uintptr_t)address, length);
    return 0;
}

static int fp_flash_erase(uint32_t address, uint32_t length)
{
    if ( !fp_flash_range_is_valid(address, length) )
    {
        return -1;
    }
    memset((void*)(uintptr_t)address, 0xFF, length);
    return 0;
}

static int fp_flash_is_xip_accessible(uint32_t address, uint32_t length)
{
    return fp_flash_range_is_valid(address, length) ? 1 : 0;
}

int fpsensor_init(void)
{
    int result = tlsf_heap_init();
    if ( result != 0 )
    {
        return -1;
    }

    fp_algorithm_platform_t platform = {
        .reset_set = fp_rstn_set,
        .chip_select_set = fp_cs_set,
        .spi_send_byte = fp_send_byte,
        .spi_receive = fp_recv_buffer,
        .delay_ms = fp_delay_ms,
        .delay_us = fp_delay_us,
        .workspace_is_accessible = fp_flash_is_xip_accessible,
        .workspace_read = fp_flash_read,
        .workspace_write = fp_flash_write,
        .workspace_erase = fp_flash_erase,
        .allocate = fp_allocate,
        .release = fp_release,
        .image_buffer = image_buf,
        .image_buffer_size = sizeof(image_buf),
        .workspace = ram_flash,
        .workspace_size = sizeof(ram_flash),
    };

    result = fp_algorithm_init(&platform);
    return result == FP_ALGORITHM_OK ? 0 : -1;
}

static int fingerprint_template_save_to_se(uint16_t template_id, uint8_t template_type,
                                           const uint8_t* template_data, size_t template_size)
{
    if ( template_data == NULL || template_size == 0U ||
         template_size > FP_TEMPLATE_STORE_SLOT_DATA_SIZE )
    {
        return -1;
    }
    if ( fp_template_store_ensure_global_head() != 0 )
    {
        logDebug("se fp store ensure global head fail");
        return -1;
    }

    uint8_t slot = 0;
    if ( fp_template_store_find_slot_for_template(template_id, &slot) != 0 )
    {
        logDebug("no available secure fingerprint slot, template_id: %d", template_id);
        return -1;
    }

    uint32_t template_len = (uint32_t)template_size;
    uint32_t aligned_len = fp_align4(template_len);
    memset(template_buf, 0, aligned_len);
    memcpy(template_buf, template_data, template_len);

    if ( !fp_template_store_write_aligned(fp_template_store_slot_data_offset(slot), template_buf, aligned_len) )
    {
        logDebug("se fp data write fail, slot: %d", slot);
        return -1;
    }

    fp_template_slot_meta_t meta = {0};
    meta.magic = FP_TEMPLATE_STORE_SLOT_MAGIC;
    meta.version = FP_TEMPLATE_STORE_FORMAT_VERSION;
    meta.template_id = template_id;
    meta.template_type = template_type;
    meta.template_len = template_len;
    meta.crc32 = fp_template_store_crc32(template_buf, template_len);
    meta.valid_marker = FP_TEMPLATE_STORE_VALID_MARK;
    meta.delete_marker = FP_TEMPLATE_STORE_NOT_DELETED_MARK;

    if ( fp_template_store_write_slot_meta(slot, &meta) != 0 )
    {
        logDebug("se fp meta write fail, slot: %d", slot);
        return -1;
    }

    logDebug("fingerprint template saved, slot: %d, id: %d, len: %lu", slot, template_id,
             (unsigned long)template_len);
    return 0;
}

static int fingerprint_template_load_from_se(void)
{
    fp_template_global_head_t head = {0};
    if ( fp_template_store_read_global_head(&head) != 0 )
    {
        logDebug("se fp store global head read fail");
        return -1;
    }
    if ( !fp_template_store_global_head_is_valid(&head) )
    {
        logDebug("se fp store global head invalid");
        return 0;
    }

    int loaded_count = 0;
    for ( uint8_t slot = 0; slot < FP_TEMPLATE_STORE_SLOT_COUNT; slot++ )
    {
        fp_template_slot_meta_t meta = {0};
        if ( fp_template_store_read_slot_meta(slot, &meta) != 0 )
        {
            logDebug("se fp slot meta read fail, slot: %d", slot);
            return -1;
        }
        if ( !fp_template_store_slot_meta_is_active(&meta) )
        {
            continue;
        }
        if ( meta.template_len == 0 || meta.template_len > FP_TEMPLATE_STORE_SLOT_DATA_SIZE )
        {
            logDebug("se fp slot len invalid, slot: %d, len: %lu", slot, (unsigned long)meta.template_len);
            continue;
        }

        uint32_t aligned_len = fp_align4(meta.template_len);
        memset(template_buf, 0, aligned_len);
        if ( !fp_template_store_read_aligned(fp_template_store_slot_data_offset(slot), template_buf, aligned_len) )
        {
            logDebug("se fp slot data read fail, slot: %d", slot);
            return -1;
        }
        uint32_t crc32 = fp_template_store_crc32(template_buf, meta.template_len);
        if ( crc32 != meta.crc32 )
        {
            logDebug(
                "se fp slot crc mismatch, slot: %d, expected: 0x%08lx, actual: 0x%08lx", slot,
                (unsigned long)meta.crc32, (unsigned long)crc32
            );
            continue;
        }

        int result = fp_algorithm_import_template(meta.template_id, meta.template_type, template_buf,
                                                  meta.template_len);
        if ( result != FP_ALGORITHM_OK )
        {
            logDebug("fingerprint template import failed: %d", result);
            continue;
        }
        loaded_count++;
    }

    logDebug("fingerprint_template_load_from_se loaded: %d", loaded_count);
    return loaded_count;
}

static int fingerprint_template_delete_from_se(uint16_t id)
{
    fp_template_global_head_t head = {0};
    if ( fp_template_store_read_global_head(&head) != 0 )
    {
        return -1;
    }
    if ( !fp_template_store_global_head_is_valid(&head) )
    {
        return 0;
    }

    for ( uint8_t slot = 0; slot < FP_TEMPLATE_STORE_SLOT_COUNT; slot++ )
    {
        fp_template_slot_meta_t meta = {0};
        if ( fp_template_store_read_slot_meta(slot, &meta) != 0 )
        {
            return -1;
        }
        if ( fp_template_store_slot_meta_is_active(&meta) && meta.template_id == id )
        {
            meta.delete_marker = FP_TEMPLATE_STORE_DELETED_MARK;
            return fp_template_store_write_slot_meta(slot, &meta);
        }
    }
    return 0;
}

static int fingerprint_template_delete_all_from_se(void)
{
    fp_template_global_head_t head = {0};
    if ( fp_template_store_read_global_head(&head) != 0 )
    {
        return -1;
    }
    if ( !fp_template_store_global_head_is_valid(&head) )
    {
        return 0;
    }

    for ( uint8_t slot = 0; slot < FP_TEMPLATE_STORE_SLOT_COUNT; slot++ )
    {
        fp_template_slot_meta_t meta = {0};
        if ( fp_template_store_read_slot_meta(slot, &meta) != 0 )
        {
            return -1;
        }
        if ( fp_template_store_slot_meta_is_active(&meta) )
        {
            meta.delete_marker = FP_TEMPLATE_STORE_DELETED_MARK;
            if ( fp_template_store_write_slot_meta(slot, &meta) != 0 )
            {
                return -1;
            }
        }
    }
    return 0;
}

int fingerprint_template_upload_from_storage(void)
{
    return fingerprint_template_load_from_se();
}

int fingerprint_template_delete_from_storage(uint16_t id)
{
    return fingerprint_template_delete_from_se(id);
}

int fingerprint_template_delete_all_from_storage(void)
{
    return fingerprint_template_delete_all_from_se();
}

/**
 * @brief Download a fingerprint template.
 *
 * Save the fingerprint template to secure-element storage.
 *
 * @param id Fingerprint ID.
 */
int fingerprint_template_download(uint16_t id)
{
    if ( id >= (uint16_t)fp_template_store_max_template_count() )
    {
        logDebug("invalid template id: %d", id);
        return -1;
    }

    size_t template_size = 0;
    uint8_t template_type = 0;
    memset(template_buf, 0, sizeof(template_buf));

    int result = fp_algorithm_export_template(id, template_buf, sizeof(template_buf), &template_size,
                                              &template_type);
    if ( result != FP_ALGORITHM_OK )
    {
        logDebug("fingerprint template export failed, id: %d, result: %d", id, result);
        return -1;
    }

    if ( fingerprint_template_save_to_se(id, template_type, template_buf, template_size) != 0 )
    {
        logDebug("fingerprint_template_download fail, id: %d", id);
        return -1;
    }

    logDebug("fingerprint_template_download ok");
    return 0;
}
