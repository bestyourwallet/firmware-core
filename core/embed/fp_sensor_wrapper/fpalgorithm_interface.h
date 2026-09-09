#ifndef FPALGORITHM_INTERFACE_H
#define FPALGORITHM_INTERFACE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define FP_ALGORITHM_VERSION_CAPACITY   32U
#define FP_ALGORITHM_IMAGE_WIDTH        96U
#define FP_ALGORITHM_IMAGE_HEIGHT       112U
#define FP_ALGORITHM_IMAGE_SIZE         (FP_ALGORITHM_IMAGE_WIDTH * FP_ALGORITHM_IMAGE_HEIGHT)
#define FP_ALGORITHM_TEMPLATE_SIZE      (12U * 1024U)
#define FP_ALGORITHM_MAX_TEMPLATE_COUNT 2U
#define FP_ALGORITHM_WORKSPACE_SIZE     (100U * 1024U)

    typedef enum
    {
        FP_ALGORITHM_OK = 0,
        FP_ALGORITHM_ERROR = -1,
        FP_ALGORITHM_NO_FINGER = -2,
        FP_ALGORITHM_BAD_IMAGE = -3,
        FP_ALGORITHM_DUPLICATE = -4,
        FP_ALGORITHM_NOT_MATCH = -5,
        FP_ALGORITHM_BUFFER_TOO_SMALL = -6,
        FP_ALGORITHM_INVALID_ARGUMENT = -7,
    } fp_algorithm_result_t;

    typedef struct
    {
        void (*reset_set)(uint8_t level);
        void (*chip_select_set)(uint8_t level);
        int (*spi_send_byte)(uint8_t value);
        int (*spi_receive)(uint8_t* buffer, uint32_t length);
        void (*delay_ms)(uint32_t milliseconds);
        void (*delay_us)(uint32_t microseconds);
        int (*workspace_is_accessible)(uint32_t address, uint32_t length);
        int (*workspace_read)(uint32_t address, uint32_t length, void* buffer);
        int (*workspace_write)(uint32_t address, const uint8_t* data, uint32_t length);
        int (*workspace_erase)(uint32_t address, uint32_t length);
        void* (*allocate)(size_t size);
        void (*release)(void* pointer);
        uint8_t* image_buffer;
        size_t image_buffer_size;
        uint8_t* workspace;
        size_t workspace_size;
    } fp_algorithm_platform_t;

    void fp_algorithm_get_version(char* version, size_t capacity);
    int fp_algorithm_init(const fp_algorithm_platform_t* platform);
    int fp_algorithm_is_finger_on(void);
    int fp_algorithm_capture_image(const uint8_t** image, uint16_t* width, uint16_t* height);
    int fp_algorithm_enroll_step(void);
    int fp_algorithm_enroll_finish(uint16_t template_id);
    void fp_algorithm_enroll_cancel(void);
    int fp_algorithm_match(uint16_t* template_id);
    int fp_algorithm_delete(uint16_t template_id);
    int fp_algorithm_delete_all(void);
    int fp_algorithm_get_template_count(uint16_t* count);
    int fp_algorithm_get_template_list(uint16_t* list, size_t capacity, size_t* count);
    int fp_algorithm_export_template(
        uint16_t template_id, uint8_t* data, size_t capacity, size_t* data_size, uint8_t* template_type
    );
    int fp_algorithm_import_template(
        uint16_t template_id, uint8_t template_type, const uint8_t* data, size_t data_size
    );
    int fp_algorithm_enter_sleep(void);
    void fp_algorithm_handle_interrupt(void);

#ifdef __cplusplus
}
#endif

#endif
