#include "fingerprint.h"

#include <stdio.h>
#include <string.h>

#include "common.h"
#include "display.h"
#include "fpalgorithm_interface.h"
#include "fpsensor_platform.h"
#include "irq.h"

#ifdef SYSTEM_VIEW
  #include "mipi_lcd.h"
  #include "systemview.h"
#endif

static bool fingerprint_module_status;
static FP_MODE current_fp_mode = FP_MODE_NORMAL;
static FP_BUTTON_STATE current_fp_button_state = FP_BUTTON_STATE_IDLE;
static bool fp_data_inited;

bool fingerprint_module_status_get(void)
{
    return fingerprint_module_status;
}

#ifdef EMULATOR

void fingerprint_get_version(char* version)
{
    if ( version != NULL )
    {
        snprintf(version, FINGERPRINT_VERSION_CAPACITY, "1.0.0");
    }
}

void fingerprint_init(void)
{
    fingerprint_module_status = true;
}

int fingerprint_detect(void)
{
    return fingerprint_module_status ? 1 : 0;
}

int fingerprint_capture_image(const uint8_t** image, uint16_t* width, uint16_t* height)
{
    if ( image == NULL || width == NULL || height == NULL )
    {
        return -1;
    }
    *image = NULL;
    *width = 0;
    *height = 0;
    return -1;
}

void fingerprint_handle_sensor_interrupt(void)
{
}

FP_RESULT fingerprint_enroll(uint8_t counter)
{
    (void)counter;
    return FP_OK;
}

int fingerprint_register_template(uint16_t id)
{
    (void)id;
    return 0;
}

int fingerprint_save(uint8_t index)
{
    (void)index;
    return 0;
}

FP_RESULT fingerprint_match(uint8_t* match_id)
{
    if ( match_id != NULL )
    {
        *match_id = 0;
    }
    return FP_OK;
}

int fingerprint_delete(uint16_t id)
{
    (void)id;
    return 0;
}

int fingerprint_delete_group(uint8_t group_id[4])
{
    (void)group_id;
    return 0;
}

int fingerprint_delete_all(void)
{
    return 0;
}

int fingerprint_get_count(uint8_t* count)
{
    if ( count == NULL )
    {
        return -1;
    }
    *count = 0;
    return 0;
}

int fingerprint_get_list(uint16_t* list, size_t capacity, uint8_t* count)
{
    if ( count == NULL || (capacity > 0U && list == NULL) )
    {
        return -1;
    }
    if ( capacity > 0U )
    {
        memset(list, 0, capacity * sizeof(*list));
    }
    *count = 0;
    return 0;
}

int fingerprint_enter_sleep(void)
{
    return fingerprint_module_status ? 0 : -1;
}

#else

void fingerprint_get_version(char* version)
{
    fp_algorithm_get_version(version, FINGERPRINT_VERSION_CAPACITY);
}

void fingerprint_init(void)
{
    ensure_ex(fp_spi_init(), 0, "fp_spi_init failed");
    ensure_ex(fp_gpio_init(), 0, "fp_gpio_init failed");
    ensure_ex(fpsensor_init(), 0, "fpsensor_init failed");
    fingerprint_module_status = true;
    ensure_ex(fingerprint_enter_sleep(), 0, "fingerprint_enter_sleep failed");
}

int fingerprint_enter_sleep(void)
{
    if ( !fingerprint_module_status || fp_algorithm_enter_sleep() != FP_ALGORITHM_OK )
    {
        return -1;
    }
    fpsensor_irq_enable();
    return 0;
}

int fingerprint_detect(void)
{
    if ( !fingerprint_module_status )
    {
        return 0;
    }
    return fp_algorithm_is_finger_on();
}

int fingerprint_capture_image(const uint8_t** image, uint16_t* width, uint16_t* height)
{
    if ( !fingerprint_module_status )
    {
        return -1;
    }
    return fp_algorithm_capture_image(image, width, height) == FP_ALGORITHM_OK ? 0 : -1;
}

void fingerprint_handle_sensor_interrupt(void)
{
    fp_algorithm_handle_interrupt();
}

FP_RESULT fingerprint_enroll(uint8_t counter)
{
    (void)counter;
    if ( !fingerprint_module_status )
    {
        return FP_ERROR_OTHER;
    }
    if ( fp_algorithm_is_finger_on() != 1 )
    {
        return FP_NO_FP;
    }

  #ifdef SYSTEM_VIEW
    const uint8_t* image = NULL;
    uint16_t width = 0;
    uint16_t height = 0;
    if ( fingerprint_capture_image(&image, &width, &height) == 0 )
    {
        display_fp(196, 500, width, height, (uint8_t*)image);
    }
  #endif

    int result = fp_algorithm_enroll_step();
    if ( result == FP_ALGORITHM_DUPLICATE )
    {
        return FP_DUPLICATE;
    }
    if ( result == FP_ALGORITHM_NO_FINGER )
    {
        return FP_NO_FP;
    }
    if ( result == FP_ALGORITHM_BAD_IMAGE )
    {
        return FP_GET_IMAGE_FAIL;
    }
    return result == FP_ALGORITHM_OK ? FP_OK : FP_ERROR_OTHER;
}

int fingerprint_register_template(uint16_t id)
{
    if ( id >= (uint16_t)fpsensor_get_max_template_count() )
    {
        return -1;
    }
    if ( fp_algorithm_enroll_finish(id) != FP_ALGORITHM_OK )
    {
        fp_algorithm_enroll_cancel();
        return -1;
    }
    if ( fingerprint_template_download(id) != 0 )
    {
        (void)fp_algorithm_delete(id);
        fp_algorithm_enroll_cancel();
        return -1;
    }
    return 0;
}

int fingerprint_save(uint8_t index)
{
    (void)index;
    return 0;
}

void fingerprint_get_group(uint8_t group[8])
{
    if ( group != NULL )
    {
        memset(group, 0xFF, 8U);
    }
}

FP_RESULT fingerprint_match(uint8_t* match_id)
{
    if ( !fingerprint_module_status || match_id == NULL )
    {
        return FP_ERROR_OTHER;
    }

    uint32_t irq = disable_irq();
    if ( fp_algorithm_is_finger_on() != 1 )
    {
        enable_irq(irq);
        return FP_NO_FP;
    }

  #ifdef SYSTEM_VIEW
    const uint8_t* image = NULL;
    uint16_t width = 0;
    uint16_t height = 0;
    if ( fingerprint_capture_image(&image, &width, &height) == 0 )
    {
        display_fp(196, 500, width, height, (uint8_t*)image);
    }
  #endif

    uint16_t matched_id = 0;
    int result = fp_algorithm_match(&matched_id);
    if ( result != FP_ALGORITHM_OK || matched_id > UINT8_MAX )
    {
        enable_irq(irq);
        return result == FP_ALGORITHM_NO_FINGER ? FP_NO_FP : FP_NOT_MATCH;
    }

    *match_id = (uint8_t)matched_id;
    enable_irq(irq);
    return FP_OK;
}

int fingerprint_delete(uint16_t id)
{
    int storage_result = fingerprint_template_delete_from_storage(id);
    if ( storage_result != 0 )
    {
        return -1;
    }
    return fp_algorithm_delete(id) == FP_ALGORITHM_OK ? 0 : -1;
}

int fingerprint_delete_group(uint8_t group_id[4])
{
    (void)group_id;
    return 0;
}

int fingerprint_delete_all(void)
{
    if ( fingerprint_template_delete_all_from_storage() != 0 )
    {
        return -1;
    }
    return fp_algorithm_delete_all() == FP_ALGORITHM_OK ? 0 : -1;
}

int fingerprint_get_count(uint8_t* count)
{
    if ( count == NULL )
    {
        return -1;
    }

    uint16_t algorithm_count = 0;
    if ( fp_algorithm_get_template_count(&algorithm_count) != FP_ALGORITHM_OK || algorithm_count > UINT8_MAX )
    {
        return -1;
    }
    *count = (uint8_t)algorithm_count;
    return 0;
}

int fingerprint_get_list(uint16_t* list, size_t capacity, uint8_t* count)
{
    if ( count == NULL || (capacity > 0U && list == NULL) )
    {
        return -1;
    }

    size_t algorithm_count = 0;
    int result = fp_algorithm_get_template_list(list, capacity, &algorithm_count);
    if ( result != FP_ALGORITHM_OK || algorithm_count > UINT8_MAX )
    {
        return -1;
    }

    *count = (uint8_t)algorithm_count;
    return 0;
}

#endif

int fpsensor_get_max_template_count(void)
{
    return FP_ALGORITHM_MAX_TEMPLATE_COUNT;
}

void fpsensor_set_config_param(uint8_t sensitivity, uint8_t area)
{
    (void)sensitivity;
    (void)area;
}

void fpsensor_get_config_param(uint32_t* sensitivity, uint16_t* area)
{
    if ( sensitivity != NULL )
    {
        *sensitivity = 0;
    }
    if ( area != NULL )
    {
        *area = 60;
    }
}

void fpsensor_clear_template_cache(bool clear_data)
{
    (void)clear_data;
}

bool fpsensor_data_version_is_new(void)
{
    return true;
}

void fpsensor_data_upgrade_prompted(void)
{
}

bool fpsensor_data_upgrade_is_prompted(void)
{
    return false;
}

void fpsensor_template_cache_clear(bool clear_data)
{
    (void)clear_data;
}

void set_fingerprint_model(FP_MODE mode)
{
    current_fp_mode = mode;
}

FP_MODE get_fingerprint_model(void)
{
    return current_fp_mode;
}

void set_fingerprint_button_state(FP_BUTTON_STATE state)
{
    current_fp_button_state = state;
}

FP_BUTTON_STATE get_fingerprint_button_state(void)
{
    return current_fp_button_state;
}

bool fpsensor_data_inited(void)
{
    return fp_data_inited;
}

static void fpsensor_load_templates(void)
{
    if ( !fp_data_inited && fingerprint_template_upload_from_storage() >= 0 )
    {
        fp_data_inited = true;
    }
}

void fpsensor_data_init_start(void)
{
    fpsensor_load_templates();
}

void fpsensor_data_init_read(void)
{
    fpsensor_load_templates();
}

void fp_test(void)
{
    display_printf("Function Test\n");
    display_printf("%s\n", __func__);
    display_printf("======================\n\n");

    uint8_t count = 0;
    uint16_t fp_list[FP_ALGORITHM_MAX_TEMPLATE_COUNT] = {0};
    uint8_t list_count = 0;

    if ( fingerprint_get_count(&count) == 0 )
    {
        display_printf("fp count: %d\n", count);
    }
    if ( fingerprint_get_list(fp_list, FP_ALGORITHM_MAX_TEMPLATE_COUNT, &list_count) == 0 )
    {
        display_printf("fp list: ");
        for ( uint8_t index = 0; index < list_count; index++ )
        {
            display_printf("%x ", fp_list[index]);
        }
        display_printf("\n");
    }
}

void fingerprint_test(void)
{
}
