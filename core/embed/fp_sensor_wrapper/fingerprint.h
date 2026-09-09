#ifndef FINGERPRINT_H
#define FINGERPRINT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define FINGERPRINT_VERSION_CAPACITY 32U

    typedef enum
    {
        FP_OK = 0,
        FP_ERROR_OTHER = 1,
        FP_DUPLICATE = 2,
        FP_GET_IMAGE_FAIL = 3,
        FP_EXTRACT_FEATURE_FAIL = 4,
        FP_NO_FP = 5,
        FP_NOT_MATCH = 6,
    } FP_RESULT;

    typedef enum
    {
        FP_MODE_NORMAL = 0,
        FP_MODE_BUTTON,
    } FP_MODE;

    typedef enum
    {
        FP_BUTTON_STATE_IDLE = 0,
        FP_BUTTON_STATE_PRESSED,
        FP_BUTTON_STATE_RELEASED,
    } FP_BUTTON_STATE;

    bool fingerprint_module_status_get(void);
    void fingerprint_get_version(char* version);
    void fingerprint_init(void);
    int fingerprint_detect(void);
    int fingerprint_capture_image(const uint8_t** image, uint16_t* width, uint16_t* height);
    void fingerprint_handle_sensor_interrupt(void);
    FP_RESULT fingerprint_enroll(uint8_t counter);
    int fingerprint_register_template(uint16_t id);
    int fingerprint_save(uint8_t index);
    FP_RESULT fingerprint_match(uint8_t* match_id);
    int fingerprint_delete(uint16_t id);
    int fingerprint_delete_group(uint8_t group_id[4]);
    int fingerprint_delete_all(void);
    int fingerprint_get_count(uint8_t* count);
    int fingerprint_get_list(uint16_t* list, size_t capacity, uint8_t* count);
    void fingerprint_get_group(uint8_t group[8]);
    int fingerprint_enter_sleep(void);
    void fingerprint_test(void);
    void fp_test(void);

    void set_fingerprint_model(FP_MODE mode);
    FP_MODE get_fingerprint_model(void);
    void set_fingerprint_button_state(FP_BUTTON_STATE state);
    FP_BUTTON_STATE get_fingerprint_button_state(void);

    int fpsensor_get_max_template_count(void);
    void fpsensor_set_config_param(uint8_t sensitivity, uint8_t area);
    void fpsensor_get_config_param(uint32_t* sensitivity, uint16_t* area);
    void fpsensor_clear_template_cache(bool clear_data);
    bool fpsensor_data_version_is_new(void);
    void fpsensor_data_upgrade_prompted(void);
    bool fpsensor_data_upgrade_is_prompted(void);
    void fpsensor_template_cache_clear(bool clear_data);

    bool fpsensor_data_inited(void);
    void fpsensor_data_init_start(void);
    void fpsensor_data_init_read(void);

#ifdef __cplusplus
}
#endif

#endif
